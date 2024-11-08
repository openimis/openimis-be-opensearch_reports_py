import graphene
import graphene_django_optimizer as gql_optimizer

from graphene_django.filter import DjangoFilterConnectionField
from django.db.models import Q
from django.contrib.auth.models import AnonymousUser

from core.schema import OrderedDjangoFilterConnectionField
from core.services import wait_for_mutation
from core.utils import append_validity_filter
from opensearch_reports.apps import OpensearchReportsConfig
from opensearch_reports.gql_mutations import UpdateOpenSearchDashboardMutation
from opensearch_reports.gql_queries import OpenSearchDashboardGQLType
from opensearch_reports.models import OpenSearchDashboard


class Query(graphene.ObjectType):
    opensearch_dashboard = OrderedDjangoFilterConnectionField(
        OpenSearchDashboardGQLType,
        orderBy=graphene.List(of_type=graphene.String),
        client_mutation_id=graphene.String(),
    )

    def resolve_opensearch_dashboard(self, info, **kwargs):
        filters = append_validity_filter(**kwargs)

        client_mutation_id = kwargs.get("client_mutation_id")
        if client_mutation_id:
            wait_for_mutation(client_mutation_id)
            filters.append(Q(mutations__mutation__client_mutation_id=client_mutation_id))
        Query._check_permissions(
            info.context.user,
            OpensearchReportsConfig.gql_opensearch_dashboard_search_perms
        )
        query = OpenSearchDashboard.objects.filter(*filters)
        return gql_optimizer.query(query, info)

    @staticmethod
    def _check_permissions(user, perms):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(perms):
            raise PermissionError("Unauthorized")


class Mutation(graphene.ObjectType):
    update_dashboard = UpdateOpenSearchDashboardMutation.Field()
