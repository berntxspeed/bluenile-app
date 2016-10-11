from ftfy import fix_text
from unidecode import unidecode

import os
import re

CSS_SRC_DIR = 'src/css'
CSS_DIST_DIR =  'css'
IMG_SRC_DIR = 'src/img'
IMG_DIST_DIR = 'img'
JS_SRC_DIR = 'src/js'
JS_DIST_DIR = 'js'
LIB_SRC_DIR = 'src/lib'
LIB_DIST_DIR = 'lib'

class UrlsUtil(object):

    def __init__(self, config, gravatar, css_manifest, img_manifest, js_manifest):
        self.config = config
        self.gravatar = gravatar
        self.css_manifest = css_manifest
        self.img_manifest = img_manifest
        self.js_manifest = js_manifest
        self.__punct_regex = re.compile(r'[\t !"#$%&\'()*\-/<=>?@\[\\\]^_`{|},.]+')

    def abs_url(self, path, secure=False):
        return "{0}/{1}".format(self.config['BASE_URL'] if not secure else
                                self.config['BASE_URL'].replace('http://', 'https://'), path)

    def static_url(self, path, secure=False):
        return '{0}/{1}'.format(self.config['STATIC_URL'] if not secure else
                                self.config['STATIC_URL'].replace('http://', 'https://'), path)

    def upload_url(self, path, secure=False):
        return '{0}/{1}'.format(self.config['UPLOAD_URL'] if not secure else
                                self.config['UPLOAD_URL'].replace('http://', 'https://'), path)

    def css_url(self, request, path, secure=False):
        if self.config['ENV'] == 'local':
            path = '{0}/{1}.css'.format(CSS_SRC_DIR, path)
        else:
            manifest_path = self.css_manifest.get('{0}.css'.format(path))
            path = '{0}{1}'.format(CSS_DIST_DIR, manifest_path or '/' + path)
            # TODO: Fix gzip files on Cloudfront.
            if self.__accepts_gzip(request):
                path += '.gz'
        return self.static_url(path, secure=secure)

    def js_url(self, request, path, secure=False):
        if self.config['ENV'] == 'local':
            path = '{0}/{1}.js'.format(JS_SRC_DIR, path)
        else:
            manifest_path = self.js_manifest.get('{0}.js'.format(path))
            path = '{0}{1}'.format(JS_DIST_DIR, manifest_path or '/' + path)
            if self.__accepts_gzip(request):
                path += '.gz'
        return self.static_url(path, secure=secure)

    def img_url(self, path, secure=False):
        if self.config['ENV'] == 'local':
            path = '{0}/{1}'.format(IMG_SRC_DIR, path)
        else:
            manifest_path = self.img_manifest.get(path)
            path = '{0}{1}'.format(IMG_DIST_DIR, manifest_path or '/' + path)
        return self.static_url(path, secure=secure)

    def lib_url(self, path, secure=False):
        dir_name = LIB_SRC_DIR if self.config['ENV'] == 'local' else LIB_DIST_DIR
        path = "{0}/{1}".format(dir_name, path)
        return self.static_url(path, secure=secure)

    def avatar_url(self, user, size='small', *args, **kwargs):
        path = None
        if user.small_avatar_key is not None and size == 'small':
            path = "%s/%s" % (self.config['AVATARS_UPLOAD_DIR'], user.small_avatar_key)
        elif user.large_avatar_key is not None and size == 'large':
            path = "%s/%s" % (self.config['AVATARS_UPLOAD_DIR'], user.large_avatar_key)
        if path is not None:
            return self.upload_url(path)
        if size == 'small':
            size = self.config['SMALL_AVATAR_SIZE']
        elif size == 'large':
            size = self.config['LARGE_AVATAR_SIZE']
        kwargs['size'] = size
        return self.gravatar(user.email, *args, **kwargs)

    def slugify(self, text, delim=u'-', default=''):
        text = str(text)
        text = fix_text(text)
        result = []
        for word in self.__punct_regex.split(text.lower()):
            result.extend(unidecode(word).split())
        slug = str(delim.join(result))
        if slug == '':
            return default
        else:
            return slug

    def __accepts_gzip(self, request):
        if not self.config['ENABLE_GZIP']:
            return False
        accept_encoding = request.headers.get('Accept-Encoding', '')
        return 'gzip' in accept_encoding.lower()
