"""Report views"""

import datetime
import time

import pytz
from django.core import urlresolvers
from django.http import HttpResponse, HttpResponseBadRequest
from django.shortcuts import redirect
from django.template.loader import get_template
from guardian.shortcuts import get_objects_for_user

from endagaweb import models
from endagaweb.models import (UserProfile, UsageEvent, Network)
from endagaweb.views.dashboard import ProtectedView


class BaseReport(ProtectedView):
    def __init__(self, reports, template, url_namespace='call-report',
                 **kwargs):
        super(BaseReport, self).__init__(**kwargs)
        self.reports = reports
        self.template = template
        self.url_namespace = url_namespace

    def handle_request(self, request):
        user_profile = UserProfile.objects.get(user=request.user)
        network = user_profile.network
        report_list = list({x for v in self.reports.itervalues() for x in v})
        if request.method == "POST":
            request.session['level_id'] = request.POST.get('level_id') or 0
            if request.session['level_id']:
                request.session['level'] = 'tower'
            else:
                request.session['level'] = "network"
                request.session['level_id'] = network.id
            request.session['reports'] = request.POST.getlist('reports', None)
            return redirect(
                urlresolvers.reverse(self.url_namespace) + '?filter=1')

        elif request.method == "GET":
            if 'filter' not in request.GET:
                # Reset filtering params.
                request.session['level'] = 'network'
                # TODO(Piyush/Shiv): Need to fix this subscriber report
                if self.url_namespace == 'subscriber-report':
                    request.session['level'] = 'network'
                request.session['level_id'] = network.id
                request.session['reports'] = report_list
        else:
            return HttpResponseBadRequest()
        timezone_offset = pytz.timezone(user_profile.timezone).utcoffset(
            datetime.datetime.now()).total_seconds()
        level = request.session['level']
        level_id = int(request.session['level_id'])
        reports = request.session['reports']

        towers = models.BTS.objects.filter(
            network=user_profile.network).values('nickname', 'uuid', 'id')
        network_has_activity = UsageEvent.objects.filter(
            network=network).exists()

        context = {
            'networks': get_objects_for_user(request.user, 'view_network',
                                             klass=Network),
            'towers': towers,
            'level': level,
            'level_id': level_id,
            'reports': reports,
            'report_list': self.reports,
            'user_profile': user_profile,
            'current_time_epoch': int(time.time()),
            'timezone_offset': timezone_offset,
            'network_has_activity': network_has_activity,
        }
        template = get_template(self.template)
        html = template.render(context, request)
        return HttpResponse(html)


class CallReportView(BaseReport):
    """View Call and SMS reports on basis of Network or tower level."""

    def __init__(self, **kwargs):
        template = "dashboard/report/call-sms.html"
        url_namespace = "call-report"
        reports = {'Call': ['Number of Calls', 'Minutes of Call'],
                   'SMS': ['Number of SMS']}
        super(CallReportView, self).__init__(reports, template,
                                             url_namespace, **kwargs)

    def get(self, request):
        return self.handle_request(request)

    def post(self, request):
        return self.handle_request(request)


class SubscriberReportView(BaseReport):
    """View Subscriber reports on basis of Network or tower level."""

    def __init__(self, **kwargs):
        template = "dashboard/report/subscriber.html"
        url_namespace = "subscriber-report"
        reports = {'Subscriber': ['Number of activations',
                                  'Number of deactivations',
                                  'Zero balance subscribers',
                                  'Inactive subscriber', 'Blocked users']}
        super(SubscriberReportView, self).__init__({}, template,
                                                   url_namespace, **kwargs)

    def get(self, request):
        return self.handle_request(request)

    def post(self, request):
        return self.handle_request(request)


class BillingReportView(BaseReport):
    """View Billing reports on basis of Network or tower level."""

    def __init__(self, *args, **kwargs):
        template = "dashboard/report/billing.html"
        url_namespace = 'billing-report'
        reports = {'Call & SMS': ['SMS Billing', 'Call and SMS Billing',
                                  'Call Billing'],
                   'Retailer': ['Retailer Recharge', 'Retailer Load Transfer'],
                   'Waterfall': ['Activation', 'Loader', 'Reload Rate',
                                 'Reload Amount', 'Reload Transaction',
                                 'Average Frequency'],
                   }
        super(BillingReportView, self).__init__(reports, template,
                                                url_namespace, **kwargs)

    def get(self, request):
        return self.handle_request(request)

    def post(self, request):
        return self.handle_request(request)


class HealthReportView(BaseReport):
    """View System health reports."""

    def __init__(self, *args, **kwargs):
        template = "404.html"  # Fix once done
        url_namespace = 'health-report'
        reports = {}
        super(HealthReportView, self).__init__(reports, template,
                                               url_namespace, **kwargs)

    def get(self, request):
        return self.handle_request(request)
