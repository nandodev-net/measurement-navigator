# Django imports
from django.test import TestCase

# Internal imports
from .models     import Input

class InputListConsistensyTest(TestCase):

    def setUp(self):
        
        Input.objects.create(asn='AS21826', input='https://voatzapi-new.nimsim.com')
        Input.objects.create(asn='AS21826', input='https://www.bloomberg.com/')
        Input.objects.create(asn='AS4048',  input='https://www.bloomberg.com/')
        Input.objects.create(asn='AS4048',  input='https://netverify.com/')

    def test_simple_add_ok(self):
        # Simple add operation, new entry with 
        # non existent values, should be available after  
        asn = 'AS4040'
        url = 'https://www.lapatilla.com'
        Input.add_input(asn, url)
        assert len(Input.objects.filter(asn=asn, input=url)) == 1, "recently added input entry should be available"

    def test_idempotent_add(self):
        # add an already existent url should be idempotent
        asn = 'AS4048'
        input='https://netverify.com/'

        Input.add_input(asn, input)
        assert len(Input.objects.filter(asn=asn, input=input)) == 1, "no duplicate entries allowed"

    def test_simple_multi_add_ok(self):
        # add multiple non existent urls
        # They should be available after the add operation
        asn1 = 'AS4040'
        url1 = 'https://www.lapatilla.com'
        asn2 = 'AS4041'
        url2 = 'https://www.lapatillo.com'
        asn3 = 'AS4042'
        url3 = 'https://www.lapatillu.com'

        inputs = [(url1, asn1), (url2, asn2), (url3, asn3)]

        Input.add_inputs(inputs) 

        assert len(Input.objects.filter(asn=asn1, input=url1)) == 1, "recently added input entry should be available"
        assert len(Input.objects.filter(asn=asn2, input=url2)) == 1, "recently added input entry should be available"
        assert len(Input.objects.filter(asn=asn3, input=url3)) == 1, "recently added input entry should be available"
        

    def test_idempotent_multi_add(self):
        # Add a couple of already existent inputs to the list,
        # no duplicates allowed
        asn1='AS21826' 
        url1='https://voatzapi-new.nimsim.com'
        asn2='AS21826'
        url2='https://www.bloomberg.com/'
        asn3 = 'AS4042'
        url3 = 'https://www.lapatillu.com'

        inputs = [(url1, asn1), (url2, asn2), (url3, asn3)]

        Input.add_inputs(inputs) 

        assert len(Input.objects.filter(asn=asn1, input=url1)) == 1, "no duplicate entries allowed"
        assert len(Input.objects.filter(asn=asn2, input=url2)) == 1, "no duplicate entries allowed"
        assert len(Input.objects.filter(asn=asn3, input=url3)) == 1, "no duplicate entries allowed"

    def test_delete(self):
        # Remove a single entry, it should not be available
        # afterwards
        asn = 'AS21826'
        url = 'https://voatzapi-new.nimsim.com'
        Input.remove_input(asn, url)

        try:
            Input.objects.get(asn=asn, input=url)
            assert False, "should not exists in the database anymore"
        except Input.DoesNotExist as _:
            pass # Everything ok


