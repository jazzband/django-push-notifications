import json
import mock
from django.test import TestCase
from django.utils import timezone
from django.contrib.auth.models import User
from push_notifications import modeldict

class ModelDictTestCase(TestCase):
    def test_model_dict_simple_cases(self):
        for k in (1,2,3,4,5):
            user = User.objects.create(
                username = 'u%s' % k,
                first_name= "user u%s" % k
            )
        md = modeldict.ModelDict('auth.User','username')
        keys = list(md.keys())
        keys.sort()
        assert tuple(keys) == ('u1','u2','u3','u4','u5')
        assert 'u2' in md
        assert 'uu2' not in md
        for k in keys:
            assert md[k]['first_name'] == "user %s" % k
        for k in keys:
            md[k] = {"last_name":"user last name %s" % k}
        for k in keys:
            assert md[k]['last_name'] == "user last name %s" % k
        assert md.get('notpresent','default') == 'default'

    def test_field_pair_dict_simple_cases(self):
        for k in (1,2,3,4,5):
            user = User.objects.create(
                username = 'u%s' % k,
                first_name= "user u%s" % k
            )
        md = modeldict.FieldPairDict('auth.User','username','first_name')
        keys = list(md.keys())
        keys.sort()
        assert tuple(keys) == ('u1','u2','u3','u4','u5')
        for k in keys:
            assert md[k] == "user %s" % k
        for k in keys:
            md[k] = "user last name %s" % k
        for k in keys:
            assert md[k] == "user last name %s" % k
        assert md.get('notpresent','default') == 'default'
