""" 
This Serverless application will be deployed as per the serverless.yml file configuration
It has various environmental variables(Tags) mentioned along with lambda permissions to do the necessary tasks

This application has two different Cloudwatch events that will trigger the lambda function
 - Nightly Schedule 
 - State Change 

 Use case: Tagging compliance Serverless application for customer's where tagging is absolutely critical for business units/ business functions. 
 Please modify as per your need

In order to run this application you'll need to download and install serverless framework dependancies

please follow the link below

https://serverless.com/framework/docs/providers/aws/guide/quick-start/

Once all dependancies are installed, you can run it as 

sls deploy --aws-profile 

Please note there are various parameters available, choose the ones necessary

"""