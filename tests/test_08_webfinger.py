import json

import pytest
from oidcmsg.exception import MissingRequiredAttribute
from oidcmsg.oidc import JRD
from oidcmsg.oidc import Link

from oidcservice.oidc import OIC_ISSUER
from oidcservice.oidc.webfinger import WebFinger
from oidcservice.service_context import ServiceContext

__author__ = 'Roland Hedberg'


def test_query():
    rel = 'http%3A%2F%2Fopenid.net%2Fspecs%2Fconnect%2F1.0%2Fissuer'
    pattern = 'https://{}/.well-known/webfinger?rel={}&resource={}'
    example_oidc = {
        'example.com': ('example.com', rel, 'acct%3Aexample.com'),
        'joe@example.com': ('example.com', rel, 'acct%3Ajoe%40example.com'),
        'example.com/joe': ('example.com', rel,
                            'https%3A%2F%2Fexample.com%2Fjoe'),
        'example.com:8080': ('example.com:8080', rel,
                             'https%3A%2F%2Fexample.com%3A8080'),
        'Jane.Doe@example.com': ('example.com', rel,
                                 'acct%3AJane.Doe%40example.com'),
        'alice@example.com:8080': ('alice@example.com:8080', rel,
                                   'https%3A%2F%2Falice%40example.com%3A8080'),
        'https://example.com': ('example.com', rel,
                                'https%3A%2F%2Fexample.com'),
        'https://example.com/joe': (
            'example.com', rel, 'https%3A%2F%2Fexample.com%2Fjoe'),
        'https://joe@example.com:8080': (
            'joe@example.com:8080', rel,
            'https%3A%2F%2Fjoe%40example.com%3A8080'),
        'acct:joe@example.com': ('example.com', rel,
                                 'acct%3Ajoe%40example.com')
        }

    wf = WebFinger(None, None)
    for key, args in example_oidc.items():
        _q = wf.query(key)
        assert _q == pattern.format(*args)


def test_query_2():
    rel = 'http%3A%2F%2Fopenid.net%2Fspecs%2Fconnect%2F1.0%2Fissuer'
    pattern = 'https://{}/.well-known/webfinger?rel={}&resource={}'
    example_oidc = {
        # below are identifiers that are slightly off
        "example.com?query": (
            'example.com', rel, 'https%3A%2F%2Fexample.com%3Fquery'),
        "example.com#fragment": (
            'example.com', rel, 'https%3A%2F%2Fexample.com'),
        "example.com:8080/path?query#fragment":
            ('example.com:8080',
             rel, 'https%3A%2F%2Fexample.com%3A8080%2Fpath%3Fquery'),
        "http://example.com/path": (
            'example.com', rel, 'http%3A%2F%2Fexample.com%2Fpath'),
        "http://example.com?query": (
            'example.com', rel, 'http%3A%2F%2Fexample.com%3Fquery'),
        "http://example.com#fragment": (
            'example.com', rel, 'http%3A%2F%2Fexample.com'),
        "http://example.com:8080/path?query#fragment": (
            'example.com:8080', rel,
            'http%3A%2F%2Fexample.com%3A8080%2Fpath%3Fquery'),
        "nov@example.com:8080": (
            "nov@example.com:8080", rel,
            "https%3A%2F%2Fnov%40example.com%3A8080"),
        "nov@example.com/path": (
            "nov@example.com", rel,
            "https%3A%2F%2Fnov%40example.com%2Fpath"),
        "nov@example.com?query": (
            "nov@example.com", rel,
            "https%3A%2F%2Fnov%40example.com%3Fquery"),
        "nov@example.com#fragment": (
            "nov@example.com", rel,
            "https%3A%2F%2Fnov%40example.com"),
        "nov@example.com:8080/path?query#fragment":(
            "nov@example.com:8080", rel,
            "https%3A%2F%2Fnov%40example.com%3A8080%2Fpath%3Fquery"),
        "acct:nov@example.com:8080": (
            "example.com:8080", rel,
            "acct%3Anov%40example.com%3A8080"
        ),
        "acct:nov@example.com/path": (
            "example.com", rel,
            "acct%3Anov%40example.com%2Fpath"
        ),
        "acct:nov@example.com?query":(
            "example.com", rel,
            "acct%3Anov%40example.com%3Fquery"
        ),
        "acct:nov@example.com#fragment": (
            "example.com", rel,
            "acct%3Anov%40example.com"
        ),
        "acct:nov@example.com:8080/path?query#fragment":(
            "example.com:8080", rel,
            "acct%3Anov%40example.com%3A8080%2Fpath%3Fquery"
        )
    }

    wf = WebFinger(None, None)
    for key, args in example_oidc.items():
        _q = wf.query(key)
        assert _q == pattern.format(*args)


def test_link1():
    link = Link(
        rel="http://webfinger.net/rel/avatar",
        type="image/jpeg",
        href="http://www.example.com/~bob/bob.jpg"
        )

    assert set(link.keys()) == {'rel', 'type', 'href'}
    assert link['rel'] == "http://webfinger.net/rel/avatar"
    assert link['type'] == "image/jpeg"
    assert link['href'] == "http://www.example.com/~bob/bob.jpg"


def test_link2():
    link = Link(rel="blog", type="text/html",
                href="http://blogs.example.com/bob/",
                titles={
                    "en-us": "The Magical World of Bob",
                    "fr": "Le monde magique de Bob"
                    })

    assert set(link.keys()) == {'rel', 'type', 'href', 'titles'}
    assert link['rel'] == "blog"
    assert link['type'] == "text/html"
    assert link['href'] == "http://blogs.example.com/bob/"
    assert set(link['titles'].keys()) == {'en-us', 'fr'}


def test_link3():
    link = Link(rel="http://webfinger.net/rel/profile-page",
                href="http://www.example.com/~bob/")

    assert set(link.keys()) == {'rel', 'href'}
    assert link['rel'] == "http://webfinger.net/rel/profile-page"
    assert link['href'] == "http://www.example.com/~bob/"


def test_jrd():
    jrd = JRD(
        subject="acct:bob@example.com",
        aliases=[
            "http://www.example.com/~bob/"
            ],
        properties={
            "http://example.com/ns/role/": "employee"
            },
        links=[
            Link(
                rel="http://webfinger.net/rel/avatar",
                type="image/jpeg",
                href="http://www.example.com/~bob/bob.jpg"
                ),
            Link(
                rel="http://webfinger.net/rel/profile-page",
                href="http://www.example.com/~bob/"
                )])

    assert set(jrd.keys()) == {'subject', 'aliases', 'properties', 'links'}


def test_jrd2():
    ex0 = {
        "subject": "acct:bob@example.com",
        "aliases": [
            "http://www.example.com/~bob/"
            ],
        "properties": {
            "http://example.com/ns/role/": "employee"
            },
        "links": [
            {
                "rel": "http://webfinger.net/rel/avatar",
                "type": "image/jpeg",
                "href": "http://www.example.com/~bob/bob.jpg"
                },
            {
                "rel": "http://webfinger.net/rel/profile-page",
                "href": "http://www.example.com/~bob/"
                },
            {
                "rel": "blog",
                "type": "text/html",
                "href": "http://blogs.example.com/bob/",
                "titles": {
                    "en-us": "The Magical World of Bob",
                    "fr": "Le monde magique de Bob"
                    }
                },
            {
                "rel": "vcard",
                "href": "https://www.example.com/~bob/bob.vcf"
                }
            ]
        }

    jrd0 = JRD().from_json(json.dumps(ex0))

    for link in jrd0["links"]:
        if link["rel"] == "blog":
            assert link["href"] == "http://blogs.example.com/bob/"
            break


def test_extra_member_response():
    ex = {
        "subject": "acct:bob@example.com",
        "aliases": [
            "http://www.example.com/~bob/"
            ],
        "properties": {
            "http://example.com/ns/role/": "employee"
            },
        'dummy': 'foo',
        "links": [
            {
                "rel": "http://webfinger.net/rel/avatar",
                "type": "image/jpeg",
                "href": "http://www.example.com/~bob/bob.jpg"
                }]
        }

    _resp = JRD().from_json(json.dumps(ex))
    assert _resp['dummy'] == 'foo'


SERVICE_CONTEXT = ServiceContext(None)


class TestWebFinger(object):
    def test_query_device(self):
        wf = WebFinger(SERVICE_CONTEXT, state_db=None)
        request_args = {'resource': "p1.example.com"}
        _info = wf.get_request_parameters(request_args)
        assert _info[
                   'url'] == 'https://p1.example.com/.well-known/webfinger' \
                             '?rel=http%3A%2F' \
                             '%2Fopenid.net%2Fspecs%2Fconnect%2F1.0%2Fissuer' \
                             '&resource=acct%3Ap1.example.com'

    def test_query_rel(self):
        wf = WebFinger(SERVICE_CONTEXT, state_db=None)
        request_args = {'resource': "acct:bob@example.com"}
        _info = wf.get_request_parameters(request_args)
        assert _info['url'] == \
               "https://example.com/.well-known/webfinger?rel=http%3A%2F%2Fopenid" \
               ".net%2Fspecs%2Fconnect%2F1.0%2Fissuer&resource=acct%3Abob" \
               "%40example.com"

    def test_query_acct(self):
        wf = WebFinger(SERVICE_CONTEXT, rel=OIC_ISSUER, state_db=None)
        request_args = {'resource': "acct:carol@example.com"}
        _info = wf.get_request_parameters(request_args=request_args)

        assert _info['url'] == \
               "https://example.com/.well-known/webfinger?rel=http%3A%2F%2Fopenid" \
               ".net%2Fspecs%2Fconnect%2F1.0%2Fissuer&resource" \
               "=acct%3Acarol%40example.com"

    def test_query_acct_resource_kwargs(self):
        wf = WebFinger(SERVICE_CONTEXT, rel=OIC_ISSUER, state_db=None)
        request_args = {}
        _info = wf.get_request_parameters(request_args=request_args,
                                          resource="acct:carol@example.com")

        assert _info['url'] == \
               "https://example.com/.well-known/webfinger?rel=http%3A%2F%2Fopenid" \
               ".net%2Fspecs%2Fconnect%2F1.0%2Fissuer&resource" \
               "=acct%3Acarol%40example.com"

    def test_query_acct_resource_config(self):
        wf = WebFinger(SERVICE_CONTEXT, rel=OIC_ISSUER, state_db=None)
        wf.service_context.config['resource'] = "acct:carol@example.com"
        request_args = {}
        _info = wf.get_request_parameters(request_args=request_args)

        assert _info['url'] == \
               "https://example.com/.well-known/webfinger?rel=http%3A%2F%2Fopenid" \
               ".net%2Fspecs%2Fconnect%2F1.0%2Fissuer&resource" \
               "=acct%3Acarol%40example.com"

    def test_query_acct_no_resource(self):
        wf = WebFinger(SERVICE_CONTEXT, rel=OIC_ISSUER, state_db=None)
        try:
            del wf.service_context.config['resource']
        except KeyError:
            pass
        request_args = {}

        with pytest.raises(MissingRequiredAttribute):
            wf.get_request_parameters(request_args=request_args)
