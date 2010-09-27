#!/usr/bin/python
# $Id:  $
"""
Databank submission test cases

$Rev: $
"""
import os, os.path
import sys
import unittest
import logging
import httplib
import urllib
try:
    # Running Python 2.5 with simplejson?
    import simplejson as json
except ImportError:
    import json
#My system is running rdflib version 2.4.2. So adding rdflib v3.0 to sys path
#sys.path.insert(0, "/home/admini/admiralTest/test/RDFDatabank/rdflib")
rdflib_path = os.path.join(os.getcwd(), 'rdflib')
sys.path.insert(0, rdflib_path)
import rdflib
from rdflib.namespace import RDF
from rdflib.graph import Graph
from rdflib.plugins.memory import Memory
from StringIO import StringIO
from rdflib import URIRef
from rdflib import Literal
rdflib.plugin.register('sparql',rdflib.query.Processor,'rdfextras.sparql.processor','Processor')
rdflib.plugin.register('sparql', rdflib.query.Result,
                       'rdfextras.sparql.query', 'SPARQLQueryResult')

if __name__ == "__main__":
    # For testing: 
    # add main library directory to python path if running stand-alone
    sys.path.append("..")

from MiscLib import TestUtils
from TestLib import SparqlQueryTestCase

from RDFDatabankConfig import RDFDatabankConfig

logger = logging.getLogger('TestSubmission')

class TestSubmission(SparqlQueryTestCase.SparqlQueryTestCase):
    """
    Test simple dataset submissions to RDFDatabank
    """
    def setUp(self):
        #super(TestSubmission, self).__init__()
        self.setRequestEndPoint(
            endpointhost=RDFDatabankConfig.endpointhost,  # Via SSH tunnel
            endpointpath=RDFDatabankConfig.endpointpath)
        self.setRequestUserPass(
            endpointuser=RDFDatabankConfig.endpointuser,
            endpointpass=RDFDatabankConfig.endpointpass)
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status="*", expect_reason="*")
        return

    def tearDown(self):
        return

    # Create empty test submission dataset
    def createTestSubmissionDataset(self):
        # Create a new dataset, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        files =[]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/", 
            expect_status=201, expect_reason="Created")
        return

    def uploadTestSubmissionZipfile(self):
        # Submit ZIP file, check response
        fields = []
        zipdata = open("data/testdir.zip").read()
        files = \
            [ ("file", "testdir.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="datasets/TestSubmission/", 
            expect_status=201, expect_reason="Created")
        return zipdata

    # Actual tests follow

    def testDatasetNotPresent(self):
        self.doHTTP_GET(resource="TestSubmission", expect_status=404, expect_reason="Not Found")

    def testDatasetCreation(self):
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Access dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        ###### print rdfdata #######
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),2,'Graph length %i' %len(rdfgraph))
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#DataSet") #####TODO: change
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        dcterms = "http://purl.org/dc/terms/"
        base = self.getRequestUri("datasets/TestSubmission/")
        self.failUnless((subj,URIRef(dcterms+"dateSubmitted"),None) in rdfgraph, 'dcterms:dateSubmitted')

    def testDatasetCreationState(self):
        pass

    def testFileUpload(self):
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),3,'Graph length %i' %len(rdfgraph))
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#DataSet") #####TODO: change
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        dcterms = "http://purl.org/dc/terms/"
        base = self.getRequestUri("datasets/TestSubmission/")
        ore  = "http://www.openarchives.org/ore/terms/"
        self.failUnless((subj,URIRef(dcterms+"dateSubmitted"),None) in rdfgraph, 'dcterms:dateSubmitted')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        # Access and check zip file content
        zipfile = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir.zip",
            expect_status=200, expect_reason="OK", expect_type="application/zip")
        self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")

    def testFileUploadState(self):
        pass

    def testFileUnpack(self):
        # Create a new dataset, check response
        self.createTestSubmissionDataset()
        # Upload zip file, check response
        zipdata = self.uploadTestSubmissionZipfile()
        # Unpack ZIP file into a new dataset, check response
        fields = \
            [ ("filename", "testdir.zip")
            ]
        ###TODO: remove? zipdata = open("data/testdir.zip").read()
        files = [ ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="items/TestSubmission", 
            expect_status=201, expect_reason="Created")
        # Access parent dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # Access and check list of contents in TestSubmission
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),4,'Graph length %i' %len(rdfgraph))
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#DataSet") #####TODO: change
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        dcterms = "http://purl.org/dc/terms/"
        base = self.getRequestUri("datasets/TestSubmission/")
        ore  = "http://www.openarchives.org/ore/terms/"
        self.failUnless((subj,URIRef(dcterms+"dateSubmitted"),None) in rdfgraph, 'dcterms:dateSubmitted')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir.zip")) in rdfgraph)
        self.failUnless((URIRef(base+"testdir.zip"),URIRef(dcterms+"hasVersion"),None) in rdfgraph, 'dcterms:hasVersion')
        # Access new dataset, check response
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir",  # dataset-zipfile: default
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission-testdir"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping") #####TODO: change
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        dcterms = "http://purl.org/dc/terms/"
        base = self.getRequestUri("datasets/TestSubmission-testdir/")
        ore  = "http://www.openarchives.org/ore/terms/"
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified') ### TODO: dcterms:created
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/test-csv.csv")) in rdfgraph)
        # Access and check content of a resource
        filedata = self.doHTTP_GET(
            resource="datasets/TestSubmission-testdir/testdir/directory/file1.b",
            expect_status=200, expect_reason="OK", expect_type="*/*")
        checkdata = open("data/testdir/directory/file1.b").read()
        self.assertEqual(filedata, checkdata, "Difference between local and remote data!")
        # Access and check zip file content
        #query_string = "SELECT ?z WHERE {<%s> <%s> ?z . }"%(subj,URIRef(dcterms+"isVersionOf"))
        #query_result = rdfgraph.query(query_string)
        #for row in query_result:
        #    zip_res = row
        #    zipfile = self.doHTTP_GET(
        #        resource=zip_res,
        #        expect_status=200, expect_reason="OK", expect_type="application/zip")
        #    self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")    

    def testInitialSubmission(self):
        # Submit ZIP file data/testdir.zip, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        zipdata = open("data/testdir.zip").read()
        files = \
            [ ("file", "testdir.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # Access versions info, check two versions exist
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'],        "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']),  2,   "Initially two versions")
        self.assertEqual(state['versions'][0],    '1', "Version 1")
        self.assertEqual(state['versions'][1],    '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'],  'xml',          "RDF file type")
        self.assertEqual(state['rdffilename'],    'manifest.rdf', "RDF file name")
        # subdir
        self.assertEqual(len(state['subdir']),    2,   "Subdirectory count")
        # Files
        # Metadata files
        # date
        # version_dates
        # Metadata
        self.assertEqual(state['metadata']['createdby'], "admin", "Created by")
        self.assertEqual(state['metadata']['embargoed'], True,      "Embargoed?")

    def testInitialSubmissionContent(self):
        # Submit ZIP file, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        zipdata = open("data/testdir.zip").read()
        files = \
            [ ("file", "testdir.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # Access and check list of contents
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        ###### print rdfdata #######
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),9,'Graph length %i' %len(rdfgraph))
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping") #####TODO: change
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        dcterms = "http://purl.org/dc/terms/"
        base = self.getRequestUri("datasets/TestSubmission/")
        ore  = "http://www.openarchives.org/ore/terms/"
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/test-csv.csv")) in rdfgraph)
        # Access and check content of a resource
        filedata = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir/directory/file1.b",
            expect_status=200, expect_reason="OK", expect_type="*/*")
        checkdata = open("data/testdir/directory/file1.b").read()
        self.assertEqual(filedata, checkdata, "Difference between local and remote data!")
        # Access and check zip file content
        query_string = "SELECT ?z WHERE {<%s> <%s> ?z . }"%(subj,URIRef(dcterms+"isVersionOf"))
        query_result = rdfgraph.query(query_string)
        for row in query_result:
            zip_res = row
            zipfile = self.doHTTP_GET(
                resource=zip_res,
                expect_status=200, expect_reason="OK", expect_type="application/zip")
            self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")

    def testUpdateSubmission(self):
        # Submit ZIP file, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        zipdata = open("data/testdir.zip").read()
        files = \
            [ ("file", "testdir.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # Access versions info, check two versions exist
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'],        "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']),  2,   "Initially two versions")
        self.assertEqual(state['versions'][0],    '1', "Version 1")
        self.assertEqual(state['versions'][1],    '2', "Version 2")
        self.assertEqual(state['currentversion'], '2', "Current version == 2")
        self.assertEqual(state['rdffileformat'],  'xml',          "RDF file type")
        self.assertEqual(state['rdffilename'],    'manifest.rdf', "RDF file name")
        # Submit ZIP file again, check response
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # Access versions info, check three versions exist
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'],        "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']),  3,   "Update gives three versions")
        self.assertEqual(state['versions'][0],    '1', "Version 1")
        self.assertEqual(state['versions'][1],    '2', "Version 2")
        self.assertEqual(state['versions'][2],    '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        self.assertEqual(state['rdffileformat'],  'xml',          "RDF file type")
        self.assertEqual(state['rdffilename'],    'manifest.rdf', "RDF file name")

    def testUpdatedSubmissionContent(self):
        # Submit ZIP file, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        zipdata = open("data/testdir.zip").read()
        files = \
            [ ("file", "testdir.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Submit ZIP file again, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        zipdata = open("data/testdir2.zip").read()
        files = \
            [ ("file", "testdir2.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        # Access and check list of contents
        state = data['state']
        parts = data['parts']
        self.assertEqual(state['item_id'],        "TestSubmission", "Submission item identifier")
        self.assertEqual(len(state['versions']),  3,   "Update gives three versions")
        self.assertEqual(state['versions'][0],    '1', "Version 1")
        self.assertEqual(state['versions'][1],    '2', "Version 2")
        self.assertEqual(state['versions'][2],    '3', "Version 3")
        self.assertEqual(state['currentversion'], '3', "Current version == 3")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),10,'Graph length %i' %len(rdfgraph))
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping") #####TODO: change
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        dcterms = "http://purl.org/dc/terms/"
        base = self.getRequestUri("datasets/TestSubmission/")
        ore = "http://www.openarchives.org/ore/terms/"
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file1.c")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir2/test-csv.csv")) in rdfgraph)
        # Access and check content of modified resource
        filedata = self.doHTTP_GET(
            resource="datasets/TestSubmission/testdir2/directory/file1.b",
            expect_status=200, expect_reason="OK", expect_type="*/*")
        checkdata = open("data/testdir2/directory/file1.b").read()
        self.assertEqual(filedata, checkdata, "Difference between local and remote data!")
        # Access and check zip file content
        query_string = "SELECT ?z WHERE {<%s> <%s> ?z . }"%(subj,URIRef(dcterms+"isVersionOf"))
        query_result = rdfgraph.query(query_string)
        for row in query_result:
            zip_res = row
            zipfile = self.doHTTP_GET(
                resource=zip_res,
                expect_status=200, expect_reason="OK", expect_type="application/zip")
            self.assertEqual(zipdata, zipfile, "Difference between local and remote zipfile!")

    def testMetadataMerging(self):
        # Submit ZIP file data/testrdf.zip, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        zipdata = open("data/testrdf.zip").read()
        files = \
            [ ("file", "testrdf.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # Access and check list of contents and metadata
        rdfdata = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/rdf+xml")
        rdfgraph = Graph()
        rdfstream = StringIO(rdfdata)
        rdfgraph.parse(rdfstream) 
        self.assertEqual(len(rdfgraph),12,'Graph length %i' %len(rdfgraph))
        subj  = URIRef(self.getRequestUri("datasets/TestSubmission"))
        stype = URIRef("http://vocab.ox.ac.uk/dataset/schema#Grouping")
        self.failUnless((subj,RDF.type,stype) in rdfgraph, 'Testing submission type: '+subj+", "+stype)
        owl = "http://www.w3.org/2002/07/owl#"
        dcterms = "http://purl.org/dc/terms/"
        base = self.getRequestUri("datasets/TestSubmission/")
        ore  = "http://www.openarchives.org/ore/terms/"
        self.failUnless((subj,URIRef(owl+"sameAs"),URIRef("http://example.org/testrdf/")) in rdfgraph, 'owl:sameAs')
        self.failUnless((subj,URIRef(dcterms+"modified"),None) in rdfgraph, 'dcterms:modified')
        self.failUnless((subj,URIRef(dcterms+"isVersionOf"),None) in rdfgraph, 'dcterms:isVersionOf')
        self.failUnless((subj,URIRef(dcterms+"title"),"Test dataset with merged metadata") in rdfgraph, 'dcterms:title')
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file1.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file1.b")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/directory/file2.a")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/test-csv.csv")) in rdfgraph)
        self.failUnless((subj,URIRef(ore+"aggregates"),URIRef(base+"testdir/manifest.rdf")) in rdfgraph)

    def testDeleteDataset(self):
        # Submit ZIP file, check response
        fields = \
            [ ("id", "TestSubmission")
            ]
        zipdata = open("data/testdir.zip").read()
        files = \
            [ ("file", "testdir.zip", zipdata, "application/zip") 
            ]
        (reqtype, reqdata) = SparqlQueryTestCase.encode_multipart_formdata(fields, files)
        self.doHTTP_POST(
            reqdata, reqtype, 
            resource="packages/", 
            expect_status=200, expect_reason="OK")
        # Access dataset, check response
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK", expect_type="application/JSON")
        # Delete dataset, check response
        self.doHTTP_DELETE(
            resource="datasets/TestSubmission", 
            expect_status=200, expect_reason="OK")
        # Access dataset, test response indicating non-existent
        data = self.doHTTP_GET(
            resource="datasets/TestSubmission", 
            expect_status=404, expect_reason="Not Found")

    def testDeleteZipFiles(self):
       data = self.doHTTP_GET(
           resource="datasets",
           expect_status=200, expect_reason="OK", expect_type="application/JSON")
       keys = data.keys()
       keys.sort()
       for i in keys:
           if (i.startswith("zipfile:")):
               self.doHTTP_DELETE(
                   resource="datasets/"+i,
                   expect_status=200, expect_reason="OK")

    # Sentinel/placeholder tests

    def testUnits(self):
        assert (True)

    def testComponents(self):
        assert (True)

    def testIntegration(self):
        assert (True)

    def testPending(self):
        assert (False), "Pending tests follow"

# Assemble test suite

def getTestSuite(select="unit"):
    """
    Get test suite

    select  is one of the following:
            "unit"      return suite of unit tests only
            "component" return suite of unit and component tests
            "all"       return suite of unit, component and integration tests
            "pending"   return suite of pending tests
            name        a single named test to be run
    """
    """
    testdict = {
        "unit":
            [ "testUnits"
            , "testDatasetNotPresent"
            , "testInitialSubmission"
            , "testInitialSubmissionContent"
            , "testUpdateSubmission"
            , "testUpdatedSubmissionContent"
            , "testMetadataMerging"
            , "testDeleteDataset"
            , "testDeleteZipFiles"
            ],
        "component":
            [ "testComponents"
            ],
        "integration":
            [ "testIntegration"
            ],
        "pending":
            [ "testPending"
            ]
        }
    """
    testdict = {
        "unit":
            [ "testUnits"
            , "testDatasetNotPresent"
            , "testDatasetCreation"
            , "testFileUpload"
            , "testFileUnpack"
            ],
        "component":
            [ "testComponents"
            ],
        "integration":
            [ "testIntegration"
            ],
        "pending":
            [ "testPending"
            ]
        }
    return TestUtils.getTestSuite(TestSubmission, testdict, select=select)

if __name__ == "__main__":
    TestUtils.runTests("TestSubmission.log", getTestSuite, sys.argv)

# End.