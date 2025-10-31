from dagster import resource

@resource 
def kafka_resource (init_config):
    # inlcude producer and consumer
    return {
        "bootstrap_servers": init_config.resource_config["bootstrap_servers"],    
    }


