import inspect
import logging
import sys

from oidcmsg import oauth2
from oidcmsg.exception import MissingParameter
from oidcmsg.key_jar import KeyJar

from oidcservice import OIDCONF_PATTERN
from oidcservice.exception import OidcServiceError
from oidcservice.service import Service

__author__ = 'Roland Hedberg'

logger = logging.getLogger(__name__)


def get_state(request_args, kwargs):
    try:
        _state = kwargs['state']
    except KeyError:
        try:
            _state = request_args['state']
        except KeyError:
            raise MissingParameter('state')

    return _state


def pick_redirect_uris(service_context, request_args=None, **kwargs):
    if 'redirect_uri' in request_args:
        pass
    elif service_context.callback:
        try:
            _response_type = request_args['response_type']
        except KeyError:
            _response_type = service_context.behaviour['response_types'][0]
            request_args['response_type'] = _response_type

        try:
            _response_mode = request_args['response_mode']
        except KeyError:
            _response_mode = ''

        if _response_mode == 'form_post':
            request_args['redirect_uri'] = service_context.callback[
                'form_post']
        elif _response_type == 'code':
            request_args['redirect_uri'] = service_context.callback['code']
        else:
            request_args['redirect_uri'] = service_context.callback[
                'implicit']
    else:
        request_args['redirect_uri'] = service_context.redirect_uris[0]
    return request_args, {}


def set_state(service_context, request_args=None, **kwargs):
    request_args['state'] = get_state(request_args, kwargs)
    return request_args, {}


class Authorization(Service):
    msg_type = oauth2.AuthorizationRequest
    response_cls = oauth2.AuthorizationResponse
    error_msg = oauth2.AuthorizationErrorResponse
    endpoint_name = 'authorization_endpoint'
    synchronous = False
    service_name = 'authorization'
    response_body_type = 'urlencoded'

    def __init__(self, service_context, client_authn_method=None, conf=None):
        Service.__init__(self, service_context,
                         client_authn_method=client_authn_method, conf=conf)
        self.pre_construct.extend([pick_redirect_uris, set_state])

    def update_service_context(self, resp, state='', **kwargs):
        self.service_context.state_db.add_response(resp, state)

    def gather_request_args(self, **kwargs):
        ar_args = Service.gather_request_args(self, **kwargs)

        if 'redirect_uri' not in ar_args:
            try:
                ar_args['redirect_uri'] = self.service_context.redirect_uris[0]
            except (KeyError, AttributeError):
                raise MissingParameter('redirect_uri')

        return ar_args


class AccessToken(Service):
    msg_type = oauth2.AccessTokenRequest
    response_cls = oauth2.AccessTokenResponse
    error_msg = oauth2.TokenErrorResponse
    endpoint_name = 'token_endpoint'
    synchronous = True
    service_name = 'accesstoken'
    default_authn_method = 'client_secret_basic'
    http_method = 'POST'
    body_type = 'urlencoded'
    response_body_type = 'json'

    def __init__(self, service_context, client_authn_method=None, conf=None):
        Service.__init__(self, service_context,
                         client_authn_method=client_authn_method, conf=conf)
        self.pre_construct.append(self.oauth_pre_construct)

    def update_service_context(self, resp, state='', **kwargs):
        self.service_context.state_db.add_response(resp, state)

    def oauth_pre_construct(self, service_context, request_args=None, **kwargs):
        _state = get_state(request_args, kwargs)
        req_args = service_context.state_db.get_response_args(
            _state, self.msg_type)

        if request_args is None:
            request_args = req_args
        else:
            request_args.update(req_args)

        if "grant_type" not in request_args:
            request_args["grant_type"] = "authorization_code"

        return request_args, {}


class RefreshAccessToken(Service):
    msg_type = oauth2.RefreshAccessTokenRequest
    response_cls = oauth2.AccessTokenResponse
    error_msg = oauth2.TokenErrorResponse
    endpoint_name = 'token_endpoint'
    synchronous = True
    service_name = 'refresh_token'
    default_authn_method = 'bearer_header'
    http_method = 'POST'

    def __init__(self, service_context, client_authn_method=None, conf=None):
        Service.__init__(self, service_context,
                         client_authn_method=client_authn_method, conf=conf)
        self.pre_construct.append(self.oauth_pre_construct)

    def update_service_context(self, resp, state='', **kwargs):
        self.service_context.state_db.add_response(resp, state)

    def oauth_pre_construct(self, service_context,request_args=None, **kwargs):
        _state = get_state(request_args, kwargs)
        req_args = service_context.state_db.get_response_args(_state,
                                                              self.msg_type)

        if request_args is None:
            request_args = req_args
        else:
            request_args.update(req_args)

        return request_args, {}


class ProviderInfoDiscovery(Service):
    msg_type = oauth2.Message
    response_cls = oauth2.ASConfigurationResponse
    error_msg = oauth2.ErrorResponse
    synchronous = True
    service_name = 'provider_info'
    http_method = 'GET'

    def __init__(self, service_context, client_authn_method=None, conf=None):
        Service.__init__(self, service_context,
                         client_authn_method=client_authn_method, conf=conf)

    def request_info(self, method="GET", request_args=None, **kwargs):

        issuer = self.service_context.issuer

        if issuer.endswith("/"):
            _issuer = issuer[:-1]
        else:
            _issuer = issuer

        return {'url': OIDCONF_PATTERN.format(_issuer)}

    def _update_service_context(self, resp, **kwargs):
        """
        Deal with Provider Config Response
        :param resp: The provider info response
        :param service_context: Information collected/used by services
        """
        issuer = self.service_context.issuer

        if "issuer" in resp:
            _pcr_issuer = resp["issuer"]
            if resp["issuer"].endswith("/"):
                if issuer.endswith("/"):
                    _issuer = issuer
                else:
                    _issuer = issuer + "/"
            else:
                if issuer.endswith("/"):
                    _issuer = issuer[:-1]
                else:
                    _issuer = issuer

            try:
                self.service_context.allow['issuer_mismatch']
            except KeyError:
                if _issuer != _pcr_issuer:
                    raise OidcServiceError(
                        "provider info issuer mismatch '%s' != '%s'" % (
                            _issuer, _pcr_issuer))

        else:  # No prior knowledge
            _pcr_issuer = issuer

        self.service_context.issuer = _pcr_issuer
        self.service_context.provider_info = resp

        for key, val in resp.items():
            if key.endswith("_endpoint"):
                for _srv in self.service_context.service.values():
                    if _srv.endpoint_name == key:
                        _srv.endpoint = val

        try:
            kj = self.service_context.keyjar
        except KeyError:
            kj = KeyJar()

        kj.load_keys(resp, _pcr_issuer)
        self.service_context.keyjar = kj

    def update_service_context(self, resp, **kwargs):
        return self._update_service_context(resp, **kwargs)


def factory(req_name, **kwargs):
    for name, obj in inspect.getmembers(sys.modules[__name__]):
        if inspect.isclass(obj) and issubclass(obj, Service):
            try:
                if obj.__name__ == req_name:
                    return obj(**kwargs)
            except AttributeError:
                pass