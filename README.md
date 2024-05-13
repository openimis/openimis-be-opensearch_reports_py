# openIMIS Backend opensearch_reports reference module

## Adding Environmental Variables to Your Build
To configure environmental variables for your build, include the following:
* `OPENSEARCH_HOST` - For the non-dockerized instance in a local context, set it to 0.0.0.0:9200. 
For the dockerized instance, use opensearch:9200.
* `OPENSEARCH_ADMIN` This variable is used for the admin username. (default value: admin)
* `OPENSEARCH_PASSWORD`  This variable is used for the admin password. (default value: admin)

## How to configure documents in openimis businesss module?
To configure Django ORM models with OpenSearch documents using a noSQL approach, follow these steps:
 * Begin by creating a `documents.py` file within your module.
 * Inside the `documents.py` file, define a Document class that corresponds to your Django ORM model. 
For example:
 ```python
from django_opensearch_dsl.registries import registry
from django_opensearch_dsl import Document, fields as opensearch_fields

@registry.register_document
class BeneficiaryDocument(Document):
    benefit_plan = opensearch_fields.ObjectField(properties={
        'code': opensearch_fields.KeywordField(),
        'name': opensearch_fields.KeywordField(),
    })
    individual = opensearch_fields.ObjectField(properties={
        'first_name': opensearch_fields.KeywordField(),
        'last_name': opensearch_fields.KeywordField(),
        'dob': opensearch_fields.DateField(),
    })
    status = opensearch_fields.KeywordField(fields={
        'status_key': opensearch_fields.KeywordField()}
    )

    class Index:
        name = 'beneficiary'  # Name of the Opensearch index
        settings = {
            'number_of_shards': 1,
            'number_of_replicas': 0
        }
        auto_refresh = True # automatically send updates and new objects to openSearch

    class Django:
        model = Beneficiary
        related_models = [BenefitPlan, Individual]
        fields = [
            'id',
        ]
        queryset_pagination = 5000
```
* In the Django class, you can use the `fields` property to include all 
the fields that are present in your Django ORM model.
* If you wish to include related fields (foreign keys), make sure to specify them 
in the `related_models` property of your Django class. Add all the foreign key fields 
that you want to include.
```python 
    class Django:
        model = Beneficiary
        related_models = [BenefitPlan, Individual]
        fields = [
            'id',
        ]
        queryset_pagination = 5000
``` 
* If you want to customize the default behavior of field creation, declare the fields you wish to modify 
using the appropriate type. For foreign keys, use the `ObjectField` type.
```python
  @registry.register_document
  class BeneficiaryDocument(Document):
      benefit_plan = opensearch_fields.ObjectField(properties={
          'code': opensearch_fields.KeywordField(),
          'name': opensearch_fields.KeywordField(),
      })
      individual = opensearch_fields.ObjectField(properties={
          'first_name': opensearch_fields.KeywordField(),
          'last_name': opensearch_fields.KeywordField(),
          'dob': opensearch_fields.DateField(),
      })
      status = opensearch_fields.KeywordField(fields={
          'status_key': opensearch_fields.KeywordField()}
      )
```
* Note that `TextField` types are typically converted to non-aggregable fields in OpenSearch. 
If you require aggregable fields, use the `KeywordField` type.
* By default, the `auto_refresh` property in the Index class should enable data to be 
automatically transferred on every CRUD operation managed by Django ORM. Ensure that 
this property is properly configured in your project.


## How to initialize data after deployment
* If you have initialized the application but still have some data to be transferred, you can effortlessly 
achieve this by using the commands available in the business module: `python manage.py add_<model_name>_data_to_opensearch`. 
This command loads existing data into OpenSearch.

## How to Import a Dashboard
* Locate the dashboard definition file in `.ndjson` format within 
the `openimis-be_<module-name>/import_data` directory.
* Log in to your OpenSearch instance.
* Expand the sidebar located on the left side of the page.
* Navigate to `Management` and select `Dashboards Management`.
* On the left side of the page, click on `Saved Objects`.
* At the top-right corner of the table, click on `Import`.
* A new side-modal will appear on the right side of the page. 
Drag and drop the file from `openimis-be_<module-name>/import_data` into the import dropzone.
* This action will import the dashboards along with related 
charts that should be accessible on the visualization page.
* Verify if the dashboards have been imported properly.

## How to Export Dashboards with Related Objects like Visualizations in OpenSearch?
* Log in to your OpenSearch instance.
* Expand the sidebar located on the left side of the page.
* Navigate to `Management` and select `Dashboards Management`.
* On the left side of the page, click on `Saved Objects`.
* At the top-right corner of the table, click on `Export <N> objects`.
* Ensure that you have selected dashboards only. Additionally, choose the option to 
include related objects, and then click export all.
* You should have downloaded file in `.ndjson` format. 
* Save file in the business model for initialization after deployment in 
`openimis-be_<module-name>/import_data`.
* Rename filename into `opensearch_<model-name>_dashboard.ndjson`

## Developer tools

### To upload opensearch configuration

- from `/openimis-be_py/openIMIS`:
  - run this command: `python manage.py upload_opensearch_dashboards --host-domain <host-domain> --imis-password <password>`. This command will This command will upload dashboards config 
  including charts, visualizations, indexes if the opensearch is available in package.
  - `<password>` - password necessary to log as admin user to obtain token to connect with API
  - `<host-domain>` is a hostname with http or https protocol for example `https://release.openimis.org`
