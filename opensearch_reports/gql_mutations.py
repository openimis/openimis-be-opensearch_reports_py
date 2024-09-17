import graphene

from django.contrib.auth.models import AnonymousUser
from django.core.exceptions import ValidationError

from core.schema import OpenIMISMutation
from core.gql.gql_mutations.base_mutation import BaseMutation, BaseHistoryModelUpdateMutationMixin

from opensearch_reports.apps import OpensearchReportsConfig
from opensearch_reports.models import OpenSearchDashboard
from opensearch_reports.service import OpenSearchDashboardService


class UpdateOpenSearchDashboardInputType(OpenIMISMutation.Input):
    id = graphene.UUID(required=True)
    name = graphene.String(required=True, max_length=255)
    url = graphene.String(required=True, max_length=255)
    synch_disabled = graphene.Boolean(required=True)


class UpdateOpenSearchDashboardMutation(BaseHistoryModelUpdateMutationMixin, BaseMutation):
    _mutation_class = "UpdateOpenSearchDashboardMutation"
    _mutation_module = "opensearch_reports"
    _model = OpenSearchDashboard

    @classmethod
    def _validate_mutation(cls, user, **data):
        if type(user) is AnonymousUser or not user.id or not user.has_perms(
                OpensearchReportsConfig.gql_opensearch_dashboard_update_perms):
            raise ValidationError("mutation.authentication_required")

    @classmethod
    def _mutate(cls, user, **data):
        if "date_valid_to" not in data:
            data['date_valid_to'] = None
        if "client_mutation_id" in data:
            data.pop('client_mutation_id')
        if "client_mutation_label" in data:
            data.pop('client_mutation_label')

        service = OpenSearchDashboardService(user)
        result = service.update(data)
        return result if not result['success'] else None

    class Input(UpdateOpenSearchDashboardInputType):
        pass
