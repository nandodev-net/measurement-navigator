from django.db import models
from django.db.models.manager import Manager
from model_utils.models import TimeStampedModel
from django.core.exceptions import ValidationError
from apps.vsf_base.vsfc_gen import VsfCodeGen
from six import python_2_unicode_compatible
import datetime
import re
import ast


class VsfBaseModel(TimeStampedModel):

    class Meta:
        abstract = True

class VsfModel(VsfBaseModel):
    """
    In order to have a vsf_code in all models, timestamps on 
    all required models, inherit from this class instead of 
    models.Model.
    """
    VSF_CODE_PREFIX = ''

    vsf_code = models.CharField(
        max_length=50,
        verbose_name= 'Codigo VSF',
        unique=True,
        blank=False,
        null=False
    )

    all_objects = Manager()

    @classmethod
    def gen_vsfc(cls):
        vsfc = VsfCodeGen()
        return vsfc.gen_vsfc(cls.VSF_CODE_PREFIX)

    @classmethod
    def copy_instance(self, cls):
        cls.id = None
        cls.vsf_code = cls.gen_vsfc()
        return cls.save()  

    def clean(self):
        now = datetime.datetime.now()
        date = now.strftime("%y%b").upper()
        # Skip O in order to avoid confusing letters
        if self.vsf_code:
            if not self.vsf_code or \
                not re.match('^%s\d{9}([A-N]|[P-Z])$' % self.VSF_CODE_PREFIX+date, str(self.vsf_code)) and \
                    not re.match('^%s\d{5}([A-N]|[P-Z])$' % self.VSF_CODE_PREFIX+date, str(self.vsf_code)):
                        raise ValidationError(
                            {'vsf_code': _('Enter a value with this format %s<5 or 9 digits><1 letter>'
                                            % self.VSF_CODE_PREFIX+date)}, code='invalid'
                        )

    class Meta:
        abstract = True