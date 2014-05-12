# -*- coding: utf-8 -*-
import datetime
from south.db import db
from south.v2 import SchemaMigration

from django.db import models
from django.conf import settings

try:
	from django.contrib.auth import get_user_model
except ImportError:  # django < 1.5
	from django.contrib.auth.models import User
else:
	User = get_user_model()

AUTH_USER_MODEL = getattr(settings, "AUTH_USER_MODEL", "auth.User")


class Migration(SchemaMigration):
	def forwards(self, orm):
		# Adding model "GCMDevice"
		db.create_table(u"push_notifications_gcmdevice", (
			("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
			("name", self.gf("django.db.models.fields.CharField")(max_length=255, null=True, blank=True)),
			("active", self.gf("django.db.models.fields.BooleanField")(default=True)),
			("user", self.gf("django.db.models.fields.related.ForeignKey")(
				to=orm["%s.%s" % (User._meta.app_label, User._meta.object_name)], null=True, blank=True)),
			("device_id", self.gf("push_notifications.fields.HexIntegerField")(null=True, blank=True)),
			("registration_id", self.gf("django.db.models.fields.TextField")()),
		))
		db.send_create_signal(u"push_notifications", ["GCMDevice"])

		# Adding model "APNSDevice"
		db.create_table(u"push_notifications_apnsdevice", (
			("id", self.gf("django.db.models.fields.AutoField")(primary_key=True)),
			("name", self.gf("django.db.models.fields.CharField")(max_length=255, null=True, blank=True)),
			("active", self.gf("django.db.models.fields.BooleanField")(default=True)),
			("user", self.gf("django.db.models.fields.related.ForeignKey")(
				to=orm["%s.%s" % (User._meta.app_label, User._meta.object_name)], null=True, blank=True)),
			("device_id", self.gf("uuidfield.fields.UUIDField")(max_length=32, null=True, blank=True)),
			("registration_id", self.gf("django.db.models.fields.CharField")(unique=True, max_length=64)),
		))
		db.send_create_signal(u"push_notifications", ["APNSDevice"])

	def backwards(self, orm):
		# Deleting model "GCMDevice"
		db.delete_table(u"push_notifications_gcmdevice")

		# Deleting model "APNSDevice"
		db.delete_table(u"push_notifications_apnsdevice")

	models = {
		u"auth.group": {
			"Meta": {"object_name": "Group"},
			"id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
			"name": ("django.db.models.fields.CharField", [], {"unique": "True", "max_length": "80"}),
			"permissions": ("django.db.models.fields.related.ManyToManyField", [],
				{"to": u"orm['auth.Permission']", "symmetrical": "False", "blank": "True"})
		},
		u"auth.permission": {
			"Meta": {"ordering": "(u'content_type__app_label', u'content_type__model', u'codename')",
				"unique_together": "((u'content_type', u'codename'),)", "object_name": "Permission"},
			"codename": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
			"content_type": ("django.db.models.fields.related.ForeignKey", [], {"to": u"orm['contenttypes.ContentType']"}),
			"id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
			"name": ("django.db.models.fields.CharField", [], {"max_length": "50"})
		},
		"%s.%s" % (User._meta.app_label, User._meta.module_name): {
			"Meta": {"object_name": User.__name__, 'db_table': "'%s'" % User._meta.db_table},
			"date_joined": ("django.db.models.fields.DateTimeField", [], {"default": "datetime.datetime.now"}),
			"email": ("django.db.models.fields.EmailField", [], {"max_length": "75", "blank": "True"}),
			"first_name": ("django.db.models.fields.CharField", [], {"max_length": "30", "blank": "True"}),
			"groups": ("django.db.models.fields.related.ManyToManyField", [],
				{"to": u"orm['auth.Group']", "symmetrical": "False", "blank": "True"}),
			"id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
			"is_active": ("django.db.models.fields.BooleanField", [], {"default": "True"}),
			"is_staff": ("django.db.models.fields.BooleanField", [], {"default": "False"}),
			"is_superuser": ("django.db.models.fields.BooleanField", [], {"default": "False"}),
			"last_login": ("django.db.models.fields.DateTimeField", [], {"default": "datetime.datetime.now"}),
			"last_name": ("django.db.models.fields.CharField", [], {"max_length": "30", "blank": "True"}),
			"password": ("django.db.models.fields.CharField", [], {"max_length": "128"}),
			"user_permissions": ("django.db.models.fields.related.ManyToManyField", [],
				{"to": u"orm['auth.Permission']", "symmetrical": "False", "blank": "True"}),
			"username": ("django.db.models.fields.CharField", [], {"unique": "True", "max_length": "30"})
		},
		u"contenttypes.contenttype": {
			"Meta": {"ordering": "('name',)", "unique_together": "(('app_label', 'model'),)", "object_name": "ContentType",
				"db_table": "'django_content_type'"},
			"app_label": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
			"id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
			"model": ("django.db.models.fields.CharField", [], {"max_length": "100"}),
			"name": ("django.db.models.fields.CharField", [], {"max_length": "100"})
		},
		u"push_notifications.apnsdevice": {
			"Meta": {"object_name": "APNSDevice"},
			"active": ("django.db.models.fields.BooleanField", [], {"default": "True"}),
			"device_id": ("uuidfield.fields.UUIDField", [], {"max_length": "32", "null": "True", "blank": "True"}),
			"id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
			"name": ("django.db.models.fields.CharField", [], {"max_length": "255", "null": "True", "blank": "True"}),
			"registration_id": ("django.db.models.fields.CharField", [], {"unique": "True", "max_length": "64"}),
			"user": ("django.db.models.fields.related.ForeignKey", [],
				{"to": u"orm['%s.%s']" % (User._meta.app_label, User._meta.object_name), "null": "True", "blank": "True"})
		},
		u"push_notifications.gcmdevice": {
			"Meta": {"object_name": "GCMDevice"},
			"active": ("django.db.models.fields.BooleanField", [], {"default": "True"}),
			"device_id": ("push_notifications.fields.HexIntegerField", [], {"null": "True", "blank": "True"}),
			"id": ("django.db.models.fields.AutoField", [], {"primary_key": "True"}),
			"name": ("django.db.models.fields.CharField", [], {"max_length": "255", "null": "True", "blank": "True"}),
			"registration_id": ("django.db.models.fields.TextField", [], {}),
			"user": ("django.db.models.fields.related.ForeignKey", [],
				{"to": u"orm['%s.%s']" % (User._meta.app_label, User._meta.object_name), "null": "True", "blank": "True"})
		}
	}

	complete_apps = ["push_notifications"]
