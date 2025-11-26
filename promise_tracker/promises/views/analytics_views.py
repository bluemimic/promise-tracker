from django.conf import settings
from django.shortcuts import render
from django.views import View

from promise_tracker.common.mixins import (
    HandleErrorsMixin,
)
from promise_tracker.common.utils import bootstrapify_form, is_htmx_request, paginate_queryset, prepare_get_params
from promise_tracker.promises.selectors.analytics_selectors import AnalyticsFilterSet, AnalyticsSelectors


class AnalyticsView(HandleErrorsMixin, View):
    template_name = "promises/analytics/analytics.html"

    def get(self, request, *args, **kwargs):
        selectors = AnalyticsSelectors()

        analytics = selectors.get_analytics(filters=request.GET)
        page_obj = paginate_queryset(request, analytics, per_page=settings.PAGINATE_BY_DEFAULT)
        querystring = prepare_get_params(request, exclude=["page"])

        filterset_cls = AnalyticsFilterSet(request.GET, queryset=None, request=request)
        filter_form = bootstrapify_form(filterset_cls.form)

        for rec in page_obj:
            total = (rec.completed_count or 0) + (rec.uncompleted_count or 0)

            if total > 0:
                rec.completed_pct = ((rec.completed_count or 0) / total) * 100
                rec.uncompleted_pct = ((rec.uncompleted_count or 0) / total) * 100
            else:
                rec.completed_pct = 0
                rec.uncompleted_pct = 0

        context = {"page_obj": page_obj, "querystring": querystring}

        if is_htmx_request(request):
            return render(request, "promises/analytics/_analytics_records.html", context)

        context.update({"filter_form": filter_form})

        return render(request, self.template_name, context)
