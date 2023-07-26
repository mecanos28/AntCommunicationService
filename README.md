# AntCommunicationService

Run the following command to start the service:

```
python3 application.py
```

Test in postman with the following request:

```
http://127.0.0.1:5000/recibir-mensaje (POST)
````

If uploaded to Beanstalk: 

```
http://antcommunicationservicev2.us-east-1.elasticbeanstalk.com/recibir-mensaje (POST)
```

Body:
```
{
    "test": "test"
}

Type: JSON
```

The response should be:

```
{
    "status": "success"
}
```

![](https://i.imgur.com/zRQe9bA.png)

## Deploy to Elastic BeanStalk (AWS)

To deploy your application to AWS Elastic Beanstalk, you need to provide your application code as a .zip file. Here's how you can create it:

1. **Gather your application files**: Make sure all the necessary files for your application are in a single directory. This usually includes your main application file (like `application.py` for a Flask app), any additional modules, and other necessary files such as a requirements.txt file which lists all the Python packages your application depends on.

2. **Create a requirements.txt file (if necessary)**: If your application depends on other Python packages, you should create a requirements.txt file that lists these packages. You can generate a requirements.txt file using pip:

    ```bash
    pip freeze > requirements.txt
    ```

   This will create a file named requirements.txt and fill it with a list of all Python packages installed in your current environment, along with their versions. If you know your application only uses specific packages, you may want to manually write the requirements.txt file and list only the necessary packages.

3. **Create the .zip file**: Navigate to the directory that contains your application files and create a .zip file. The way to do this depends on your operating system:

    - On Windows, you can select all files, right-click, and choose Send to > Compressed (zipped) folder.
    
    - On macOS, you can select all files, right-click, and choose Compress Items.

    - On Linux, you can use the zip command:
  
      ```bash
      zip ../myapp.zip *
      ```
      This command will create a file named myapp.zip in the parent directory, containing all files in the current directory.

    In all cases, ensure that you don't include any top-level directory. When Elastic Beanstalk extracts your .zip file, it should directly see your application files, not a single directory containing them.

4. **Upload the .zip file to Elastic Beanstalk**: When you're creating a new Elastic Beanstalk environment (or a new application version for an existing environment), you can choose to "Upload your code", and then you can upload the .zip file you've just created.

Keep in mind that the application file (the file that contains your Flask application, usually named `application.py` or `application.py`) and the `requirements.txt` file (if you have one) should be in the root of the .zip file, not in a subdirectory.

You might also need to add a file named `.ebextensions/python.config` to your .zip file with the following content, to ensure Elastic Beanstalk uses the correct file and function to start your Flask application:

```yaml
option_settings:
  aws:elasticbeanstalk:container:python:
    WSGIPath: application.py
```



Replace `application.py` with the path to your application file if it's different. This file should be in the same directory as your main Flask file.