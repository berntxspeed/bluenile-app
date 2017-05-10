import pysftp
import zipfile as ZF
from zipfile import BadZipFile
import os
import csv
import shutil

from .db_data_loader import SqlDataLoader
from ....common.utils.db_datatype_handler import set_db_instance_attr

tmp_directory = 'tmp'
if not os.path.isdir(tmp_directory):
    os.mkdir(tmp_directory)

class FtpFile(object):

    def __init__(self, file, ftp_path, ftp_cfg):

        """docstring"""

        self._file = file
        self._path = ftp_path
        self._ftp_cfg = ftp_cfg


    def filename(self):
        return self._file


    def download(self):

        """Download the file from the FTP"""

        try:
            with pysftp.Connection(
                    host=self._ftp_cfg['host'],
                    username=self._ftp_cfg['username'],
                    password=self._ftp_cfg['password']
            ) as srv:
                with pysftp.cd(tmp_directory):
                    srv.get(self._path + self._file)

        except (pysftp.SSHException, AttributeError) as exc:
            raise ConnectionRefusedError('failed to connect to ftp, and thus cannot download file: {}'.format(str(exc)))
        except FileNotFoundError:
            raise FileNotFoundError('could not find file on server with filename: {} and directory: {}'.format(self._file, self._path))

class CsvFile(SqlDataLoader, FtpFile):

    def __init__(self, file, db_session, db_model, primary_keys, db_field_map, ftp_path=None, ftp_cfg=None, file_encoding='utf8', delimiter=None):

        """Instantiates the Csvfile class

        Args:
            file = filename ex. "file.txt"
            db_session = db session object
            db_model = db model object of the destination db table
            primary_keys = list of strings representing db primary key field names
            db_field_map = dict of key, value = db_field, csv_field mappings
            ftp_path = path to file on ftp ex. "folder/"
            ftp_cfg should be a dict with keys host, username, and password

        Returns:
            instance of the Csvfile class
        """


        SqlDataLoader.__init__(self, db_session, db_model, primary_keys)
        self._no_dl = True
        self._filename = file

        if ftp_path and ftp_cfg:
            FtpFile.__init__(self, file, ftp_path, ftp_cfg)
            self._no_dl = False

        if delimiter:
            self._delimiter = delimiter
        else:
            self._delimiter = ','

        self._db_field_map = db_field_map

        self._file_encoding = file_encoding

    def load_data(self):
        if not self._no_dl:
            FtpFile.download(self)

        SqlDataLoader.load_to_db(self, self._get_data, delimiter=self._delimiter)

    def _get_data(self, chunk_size=10000, delimiter=','):
        num_recs = 0
        filename = self._filename
        """Load csv file into the database

        Args:
            filename: name of file to load to db
            db_model: Sqlalchemy model of table to be loaded into
            primary_keys: list of strings denoting primary key fields of table to respect
            db_field_map: dict of string pairs denoting csvfields mapping to dbfields

        Returns:
            none

        Usage:
            load_to_db(filename=filename, db_model=dbModel, primary_keys=['primaryKeyField'], db_field_map={
                'csvField1': 'dbField1',
                'csvField2': 'dbField2',
                'csvField3': 'dbField3'
            })

        Raises:
            FileNotFoundError: if file isn't found (can happen if this method is run before file(s) has(ve) been downloaded
            KeyError: if a key on CSV file cannot be found
        """
        try:
            os.chdir(tmp_directory)
            try:
                with open(filename, 'r', encoding=self._file_encoding) as csvfile:
                    csvfile_reader = csv.DictReader(csvfile, delimiter=delimiter)
                    # create a dict of all the new records by their primary key
                    import_items = {}
                    for row in csvfile_reader:
                        item = SqlDataLoader.db_model(self)
                        for db_field, csv_field in self._db_field_map.items():
                            try:
                                set_val = set_db_instance_attr(item, db_field, row[csv_field])
                                item.__setattr__(db_field,set_val)
                            except Exception as exc:
                                print('failed to set attr: '+str(db_field)+'<>'+str(row[csv_field])+' exc: '+str(exc))
                        # use a composite key to reference the records on the dict
                        composite_key = ''
                        invalid_comp_key = False
                        for pk in self._primary_keys:
                            if str(getattr(item, pk)) is None or len(str(getattr(item, pk))) < 1 or str(getattr(item, pk)) == '':
                                invalid_comp_key = True
                            composite_key += str(getattr(item, pk))
                        # place item on dict, w key reference to composite key, and value of dbModel instance
                        if not invalid_comp_key:
                            try:
                                import_items[composite_key] = item._add_metadata()
                            except Exception as exc:
                                print('problem calculating metadata for '+str(composite_key)+' : message:'+str(exc))
                        else:
                            pass
                            #print('invalid composite key value: ' + str(composite_key))
                        if num_recs == 0:
                            print('starting load to db...')

                        num_recs += 1
                        if num_recs >= chunk_size:
                            num_recs = 0
                            yield (False, import_items)
                            import_items = {}


            except FileNotFoundError as exc:
                raise FileNotFoundError('could not locate file: {}, error: {}'.format(filename, str(exc)))
            except KeyError as exc:
                raise KeyError(str(exc))

            os.chdir('..')
            yield (True, import_items)
        except Exception as exc:
            os.chdir('..')
            raise exc

    def clean_up(self):

        try:
            os.chdir(tmp_directory)
            os.remove(self._filename)
        finally:
            os.chdir('..')


class ZipFile(FtpFile):

    """
    Usage:
    -instantiate: zf = Zipfile("filename.zip", "/ftp/path", ftp_cfg)
    where ftp_cfg = {'host': 'ftp.site.com', 'username': 'uname', 'password': 'passwd'}
    -download/unzip: zf.download()
    -import desired files to db:
    """

    def __init__(self, file, ftp_path, ftp_cfg):

        FtpFile.__init__(self, file, ftp_path, ftp_cfg)

        if file.split('.')[-1] != 'zip':
            raise ValueError('file type must be zip')

        self._extracted_files_dir = ''
        self._extracted_files = []
        self._downloaded_yet = False


    def extracted_files(self):
        return self._extracted_files


    def _extract_zip(self):

        dest_dir = FtpFile.filename(self).split('.')[0] + '_EXTRACTED_FILES'

        try:
            os.chdir(tmp_directory)
            try:
                with ZF.ZipFile(FtpFile.filename(self), 'r') as zf:
                    if not os.path.isdir(dest_dir):
                        os.mkdir(dest_dir)
                    zf.extractall(dest_dir + '/.')
            except FileNotFoundError:
                print("File Not Found.")
            except BadZipFile as err:
                print("BadZipType: ", err)

            self._extracted_files_dir = dest_dir
            self._extracted_files = [file.name for file in os.scandir(dest_dir) if file.is_file() and len(file.name.split('.')[-1]) > 0]
        finally:
            os.chdir('..')

    def load_data(self, file, db_session, db_model, primary_keys, db_field_map):

        if not self._downloaded_yet:
            FtpFile.download(self)
            self._extract_zip()
            self._downloaded_yet = True

        if file not in self._extracted_files:
            raise ValueError('requested file: ' + file + ' is not contained in extracted files list')

        file = self._extracted_files_dir + '/' + file
        if file.split('.')[-1] == 'csv':
            cf = CsvFile(file, db_session, db_model, primary_keys, db_field_map)
            cf.load_data()
        else:
            raise TypeError('requested file type is not supported yet.  current support: csv')

    def clean_up(self):

        try:
            os.chdir(tmp_directory)

            shutil.rmtree(self._extracted_files_dir)
            os.remove(self._file)
        finally:
            os.chdir('..')
