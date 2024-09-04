__version__ = "1.0.0"


# This is needed to allow Airflow to pick up specific metadata fields it needs for certain features.
def get_provider_info():
    return {
        "package-name": "airflow-provider-truefoundry",  # Required
        "name": "TrueFoundry",  # Required
        "description": "A True Foundry Airflow provider.",  # Required
        "connection-types": [
            {
                "connection-type": "truefoundry",
                "hook-class-name": "truefoundry_provider.hooks.truefoundry.TrueFoundryHook"
            }
        ],
        "extra-links": ["truefoundry_provider.operators.job_run_now.TrueFoundryOperatorExtraLink"],
        "versions": [__version__],  # Required
    }
