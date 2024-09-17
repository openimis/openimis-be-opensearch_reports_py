import graphene
from graphene_django import DjangoObjectType

from core import ExtendedConnection
from opensearch_reports.models import OpenSearchDashboard


class OpenSearchDashboardGQLType(DjangoObjectType):
    uuid = graphene.String(source='uuid')

    class Meta:
        model = OpenSearchDashboard
        interfaces = (graphene.relay.Node,)
        filter_fields = {
            "id": ["exact"],
            "name": ["iexact", "istartswith", "icontains"],
            "url": ["iexact", "istartswith", "icontains"],
            "synch_disabled": ["exact"],

            "date_created": ["exact", "lt", "lte", "gt", "gte"],
            "date_updated": ["exact", "lt", "lte", "gt", "gte"],
            "is_deleted": ["exact"],
            "version": ["exact"],
        }
        connection_class = ExtendedConnection
