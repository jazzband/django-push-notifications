from django.apps import apps
from collections import MutableMapping

try:
	basestring
except:
	basestring = str


class ModelDict(MutableMapping):
	def __init__(self, model, key_field):
		self._model = model
		self._key = key_field

	def _fix_model(self):
		if isinstance(self._model, basestring):
			self._model = apps.get_model(*self._model.split('.', 1))

	def _get_value(self, o):
		return {f.name: getattr(o, f.name) for f in o._meta.fields}

	def _set_value(self, o, value):
		for k in value:
			# some inconsistency with natural dict: ignore absence instead of deleting;
			# use None to clean the field value instead
			setattr(o, k, value[k])
		o.save()

	def get(self, key, *d):
		self._fix_model()
		q = self._model.objects.filter(**{self._key: key})
		if q:
			return self._get_value(q[0])
		if len(d):
			return d[0]
		raise KeyError("No such key in the database")

	def has_key(self, key):
		self._fix_model()
		q = self._model.objects.filter(**{self._key: key})
		return bool(q)

	def set(self, key, value):
		self._fix_model()
		q = self._model.objects.filter(**{self._key: key})
		if q:
			o = q[0]
		else:
			o = self._model(**{self._key: key})
		self._set_value(o, value)

	def remove(self, key):
		self._fix_model()
		self._model.objects.filter(**{self._key: key}).delete()

	def __getitem__(self, key):
		return self.get(key)

	def __setitem__(self, key, value):
		return self.set(key, value)

	def __delitem__(self, key):
		return self.remove(key)

	def __iter__(self):
		self._fix_model()
		for o in self._model.objects.all():
			yield getattr(o, self._key)

	def __len__(self):
		self._fix_model()
		return self._model.objects.count()


class FieldPairDict(ModelDict):
	def __init__(self, model, key_field, value_field):
		ModelDict.__init__(self, model, key_field)
		self._value = value_field
		if '.' in self._value:
			self._value = self._value.split('.')
		elif '__' in self._value:
			self._value = self._value.split('__')
		else:
			self._value = [self._value]

	def _get_value(self, o, path=None):
		if path is None:
			path = self._value
		v = ModelDict._get_value(self, o)[path[0]]
		path = path[1:]
		if not path:
			return v
		return self._get_value(v, path)

	def _set_value(self, o, value):
		if len(self._value) > 1:
			raise AttributeError("Dict assignment over relations is ambiguous")
		setattr(o, self._value[0], value)
		o.save()
