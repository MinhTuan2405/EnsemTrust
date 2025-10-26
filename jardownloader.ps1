# Create jars directory if it doesn't exist
New-Item -ItemType Directory -Force -Path "./jars"

# Download the JAR files
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-aws/3.3.4/hadoop-aws-3.3.4.jar" -OutFile "./jars/hadoop-aws-3.3.4.jar"
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/org/apache/hadoop/hadoop-common/3.3.4/hadoop-common-3.3.4.jar" -OutFile "./jars/hadoop-common-3.3.4.jar"
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/org/postgresql/postgresql/42.7.8/postgresql-42.7.8.jar" -OutFile "./jars/postgresql-42.7.8.jar"
Invoke-WebRequest -Uri "https://repo1.maven.org/maven2/com/amazonaws/aws-java-sdk-bundle/1.12.767/aws-java-sdk-bundle-1.12.767.jar" -OutFile "./jars/aws-java-sdk-bundle-1.12.767.jar"