from rest_framework import serializers, permissions, viewsets
from .models import APNSDevice, GCMDevice


class IsOwner(permissions.BasePermission):
    """
    Custom permission to only allow owners of an object to see it.
    """

    def has_object_permission(self, request, view, obj):
        # Only allow the user to see their own devices
        return obj.user == request.user


class APNSDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = APNSDevice
        fields = ('name', 'device_id', 'registration_id')

    read_only = ('date_created',)


class GCMDeviceSerializer(serializers.ModelSerializer):
    class Meta:
        model = GCMDevice
        fields = ('name', 'device_id', 'registration_id')

    read_only = ('date_created',)


class DeviceViewSetMixin(object):
    lookup_field = 'registration_id'
    queryset = APNSDevice.objects.all()
    serializer_class = APNSDeviceSerializer
    permission_classes = (permissions.IsAuthenticated,
                          IsOwner,)

    def pre_save(self, obj):
        # Set the requesting user as the device user
        obj.user = self.request.user


class APNSDeviceViewSet(DeviceViewSetMixin, viewsets.ModelViewSet):
    queryset = APNSDevice.objects.all()
    serializer_class = APNSDeviceSerializer


class GCMDeviceViewSet(DeviceViewSetMixin, viewsets.ModelViewSet):
    queryset = GCMDevice.objects.all()
    serializer_class = GCMDeviceSerializer


#
# Links for viewsets
#
apns_list = APNSDeviceViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

apns_detail = APNSDeviceViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})

gcm_list = GCMDeviceViewSet.as_view({
    'get': 'list',
    'post': 'create'
})

gcm_detail = GCMDeviceViewSet.as_view({
    'get': 'retrieve',
    'delete': 'destroy'
})
