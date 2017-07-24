from flask import jsonify, Response, send_from_directory, send_file
from premailer import transform
import json
# from PIL import Image, ImageDraw
from urllib.parse import urlsplit
import os
import base64
from io import BytesIO

from tempfile import NamedTemporaryFile
from shutil import copyfileobj
from os import remove

from .classes.esp_push import EmlPush, ImgPush
from ...common.models.user_models import Upload, Template


class EmailService(object):

    def __init__(self, config, db_session, logger):
        self.config = config
        self.db_session = db_session
        self.logger = logger

    @staticmethod
    def validate_on_submit(request, form):
        return request.method == 'POST' and form.validate()

    def download(self, request):
        html = transform(request.form.get('html', None))
        action = request.form.get('action', None)
        if action == 'download':
            filename = request.POST['filename']
            content_type = "text/html"
            content_disposition = "attachment; filename=%s" % filename
            response = jsonify(html=html, content_type=content_type, content_disposition=content_disposition)
            response['Content-Disposition'] = content_disposition
        elif action == 'email':
            print('attempting to send email...')
            """to = request.POST['rcpt']
            subject = request.POST['subject']
            from_email = settings.DEFAULT_FROM_EMAIL
            # TODO: convert the HTML email to a plain-text message here.  That way
            # we can have both HTML and plain text.
            msg = ""
            send_mail(subject, msg, from_email, [to], html_message=html, fail_silently=False)
            # TODO: return the mail ID here"""
            response = jsonify(status='sent')
        return response, 200

    def upload(self, request):
        if request.method == 'POST':
            file = request.files['files[]']
            if file:
                print('found file')
                filename = file.filename
                print('uploaded filename: ' + filename)
                img = ImgPush(self.db_session, file, filename)
                resp, http_status_code = img.save()
                return jsonify(files=[resp]), http_status_code
            else:
                return jsonify('no file given'), 404
        else:
            return jsonify('not post upload')

    def image(self, request):
        logger = self.logger
        logger.debug("request.method: %r", request.method)
        if request.method == 'GET':
            method = request.args.get('method', None)
            print("method: %r", method)
            params = request.args.get('params', None).split(',')
            print("params: %r", params)
            if method == 'placeholder':
                height, width = [self.__size(p) for p in params]
                image = self.__get_placeholder_image(height, width)
            elif method == 'cover':
                src = request.args.get('src', None)
                width, height = [self.__size(p) for p in params]
                upload = Upload.query.filter_by(esp_hosted_url=src).first()
                if upload is None:
                    raise ValueError('no matching image found in db')
                image = Image.open(BytesIO(upload.image))
                if width is not None and height is not None:
                    image.thumbnail((width, height), Image.ANTIALIAS)
            elif method == 'resize':
                src = request.args.get('src', None)
                width, height = [self.__size(p) for p in params]
                upload = Upload.query.filter_by(esp_hosted_url=src).first()
                if upload is None:
                    raise ValueError('no matching image found in db')
                image = Image.open(BytesIO(upload.image))
                if not width:
                    width = upload.image_size_width
                if not height:
                    height = upload.image_size_height
                image.thumbnail((width, height), Image.ANTIALIAS)
            file = BytesIO()
            image.save(file, "PNG")
            file.seek(0)
            return send_file(file, mimetype='image/png')

    def template(self, request):
        action = request.form.get('action', None)
        if action == 'save':
            print('doing save')
            key = request.form.get('key', None)
            name = request.form.get('name', None)
            html = request.form.get('html', None)
            template_data = json.loads(request.form.get('template_data', None))
            meta_data = json.loads(request.form.get('meta_data', None))

            if key is not None:
                template = Template.query.filter_by(key=key).first()
            else:
                template = Template.query.filter_by(name=name).first()
            if template is None:
                template = Template()

            if name is not None:
                template.name = name
            template.html = html
            template.template_data = template_data
            template.meta_data = meta_data

            self.db_session.add(template)
            self.db_session.commit()
            return jsonify(status='template saved', key=str(template.key)), 200
        elif action == 'load':
            key = request.form.get('key', None)
            if key is None:
                raise ValueError('key cannot be empty')
            template = Template.query.filter_by(key=key).first()
            if template is not None:
                return jsonify(content=template.template_data, meta_data=template.meta_data)
            else:
                return jsonify(status='template not found'), 404
        elif action == 'push-to-ems':
            print('executing push of email to EMS')
            key = request.form.get('key', None)
            if key is None:
                raise ValueError('name cannot be empty')
            print('pushing email with key: ' + key + ' to SFMC...')
            eml = EmlPush(key)
            resp = eml.sync_to_ems()
            return jsonify(results=resp.message), resp.code
        else:
            return jsonify("unknown action"), 400

    @staticmethod
    def __get_placeholder_image(width, height):
        image = Image.new("RGB", (width, height))
        draw = ImageDraw.Draw(image)
        draw.rectangle([(0, 0), (width, height)], fill=(0x70, 0x70, 0x70))
        # stripes
        x = 0
        y = 0
        size = 40
        while y < height:
            draw.polygon([(x, y), (x + size, y), (x + size * 2, y + size), (x + size * 2, y + size * 2)],
                         fill=(0x80, 0x80, 0x80))
            draw.polygon([(x, y + size), (x + size, y + size * 2), (x, y + size * 2)], fill=(0x80, 0x80, 0x80))
            x = x + size * 2
            if (x > width):
                x = 0
                y = y + size * 2
        return image

    @staticmethod
    def __size(size_txt):
        if size_txt == 'null':
            return None
        else:
            return int(size_txt)
