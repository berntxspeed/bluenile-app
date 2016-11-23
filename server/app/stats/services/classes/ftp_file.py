import pysftp
import zipfile as ZF
from zipfile import BadZipFile
import os
import csv

from .db_data_loader import SqlDataLoader


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
                    password=self._ftp_cfg['password']) as srv:
                with pysftp.cd(tmp_directory):
                    srv.get(self._path + self._file)

        except (pysftp.SSHException, AttributeError) as exc:
            raise ConnectionRefusedError('failed to connect to ftp, and thus cannot download file: {}'.format(str(exc)))
        except FileNotFoundError:
            raise FileNotFoundError(
                'could not find file on server with directory: {} and filename: {}'
                    .format(self._file, self._path))
        

class CsvFile(SqlDataLoader, FtpFile):

    def __init__(self, file, db_session, db_model, primary_keys, db_field_map, ftp_path=None, ftp_cfg=None):

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

        if file.split('.')[-1] != 'csv':
            raise ValueError('filetype must be csv')

        SqlDataLoader.__init__(self, db_session, db_model, primary_keys)
        self._no_dl = True
        self._filename = file

        if ftp_path and ftp_cfg:
            FtpFile.__init__(self, file, ftp_path, ftp_cfg)
            self._no_dl = False

        self._db_field_map = db_field_map

    def load_data(self):
        if not self._no_dl:
            FtpFile.download(self)

        data = self._get_data(self._filename)
        SqlDataLoader.load_to_db(self, data)

    def _get_data(self, filename, delimiter=','):

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
                with open(filename, 'r') as csvfile:
                    csvfile_reader = csv.DictReader(csvfile, delimiter=delimiter)
                    # create a dict of all the new records by their primary key
                    import_items = {}
                    for row in csvfile_reader:
                        item = SqlDataLoader.db_model(self)
                        for csv_field, db_field in self._db_field_map.items():
                            item.__setattr__(db_field, row[csv_field])
                        # use a composite key to reference the records on the dict
                        composite_key = ''
                        for pk in self._primary_keys:
                            composite_key += getattr(item, pk)
                        # place item on dict, w key reference to composite key, and value of dbModel instance
                        import_items[composite_key] = item
            except FileNotFoundError as exc:
                raise FileNotFoundError('could not locate file: {}, error: {}'.format(filename, str(exc)))
            except KeyError as exc:
                raise KeyError(str(exc))

            return import_items
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
