# PDPrognosis

<img src="./static/PD.jpeg" width='400'>
<h2>Introduction</h1>
<p>PDPrognosis is a graduation project that offers a user-friendly platform designed to streamline the management of Parkinson's disease for doctors. It provides time-saving tools and comprehensive insights into patients' protein and peptide profiles, aiding doctors in making informed decisions with ease, and ensures all relevant information is readily accessible for effective patient care.</p>
<h2>Technology</h1> 
<ul>
<li>Digital Ocean hosting services.</li>
<li>Visual Studio Code</li>
<li>Python</li>
<li>Html</li>
<li>CSS</li>
<li>JavaScript</li>
</ul>
<section id="launching-instructions">
    <h2>🚀 Launching Instructions</h2>
    <p>Follow these simple steps to launch and experience the project:</p>

    <h3>1️⃣ Clone the Repository</h3>
    <p>Start by cloning this repository to your local machine:</p>
    <pre><code>git clone https://github.com/your-username/your-repo-name.git
cd your-repo-name</code></pre>

    <h3>2️⃣ Install Dependencies</h3>
    <p>Make sure you have Python (or any required environment) installed. Then, install the necessary dependencies:</p>
    <pre><code>pip install -r requirements.txt</code></pre>

    <h3>3️⃣ Set Up the Database</h3>
    <p>Initialize the database for the project (if applicable). Run the following commands:</p>
    <pre><code>flask db init
flask db migrate
flask db upgrade</code></pre>
    <p>Ensure you have the required <code>.env</code> or configuration file in place.</p>

    <h3>4️⃣ Start the Application</h3>
    <p>Launch the application with a single command:</p>
    <pre><code>flask run</code></pre>
    <p>The application will now be available at: <a href="http://127.0.0.1:5000" target="_blank">http://127.0.0.1:5000</a></p>

    <h3>5️⃣ Explore the Features</h3>
    <ul>
        <li>Log in to access your personalized dashboard.</li>
        <li>Navigate to explore key functionalities like:</li>
        <ul>
            <li>Patient Management</li>
            <li>UPDRS Predictions</li>
            <li>Protein Analysis</li>
            <li>Data Visualization</li>
        </ul>
    </ul>
    <p>Enjoy exploring how our project revolutionizes Parkinson's management! 🌟</p>

    <h3>💡 Tips for First-Time Users</h3>
    <ul>
        <li>Make sure your <code>config.json</code> (or <code>.env</code>) file has all the correct credentials.</li>
        <li>If you're working with an SQLite database, ensure the <code>patients_data.db</code> file exists in the root directory.</li>
        <li>For troubleshooting, refer to the <a href="#faq">FAQ</a> section below.</li>
    </ul>

    <h3>🧑‍💻 Developer Mode</h3>
    <p>Want to make changes or debug the project? Use developer mode:</p>
    <pre><code>flask run --debug</code></pre>
    <p>This enables live reloading and error tracking.</p>

    <h3>🌐 Deployment</h3>
    <p>When you're ready to deploy the project to production:</p>
    <ul>
        <li>Use a web server like Gunicorn or a platform like Heroku, AWS, or Azure.</li>
        <li>Update the environment variables in your deployment environment.</li>
    </ul>
    <p>For a detailed guide, refer to the <a href="#deployment-guide">Deployment Guide</a>.</p>
</section>

