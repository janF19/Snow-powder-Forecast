

const express = require('express');
const path = require('path');
const dotenv = require('dotenv');
const axios = require('axios');
const resortRoutes = require('./routes/resorts');



const cron = require('node-cron');

const { exec } = require('child_process');
const fs = require('fs');

// Initialize the app and configure environment variables
dotenv.config();
const app = express();

// Set up middleware
app.use(express.json());
app.use(express.static(path.join(__dirname, 'public')));
app.use(express.urlencoded({ extended: true }));

// View engine setup (optional - for rendering HTML)
app.set('views', path.join(__dirname, 'views'));
app.set('view engine', 'ejs');  // You can also use Pug, Handlebars, etc.

// Serve static files from the 'styles' directory
app.use('/styles', express.static(path.join(__dirname, 'styles')));


// Use resort routes (handles the home route as well)
app.use('/', resortRoutes);  // Home route is now part of resortRoutes





// Start the server
const PORT = process.env.PORT || 3002;
app.listen(PORT, '0.0.0.0', () => {
    console.log(`Server running on port ${PORT}`);
});


const scriptPath = path.join(__dirname, 'getForecastFull_all_resorts.py')
const dataDir = process.env.DATA_DIR || __dirname;
const jsonPath = path.join(__dirname, 'weather_dataFull_7.json')

if (!fs.existsSync(dataDir)) {
    fs.mkdirSync(dataDir, { recursive: true });
}

function fetchWeatherData() {
    console.log('Starting weather data fetch...');
    console.log('Script path:', scriptPath);
    console.log('JSON output path:', jsonPath);

    // First, check Python installation
    exec('which python3', (error, stdout, stderr) => {
        if (error) {
            console.error('Error finding Python:', error);
            return;
        }
        const pythonPath = stdout.trim();
        console.log('Python path:', pythonPath);

        // Also check installed packages
        exec(`${pythonPath} -m pip list`, (error, stdout, stderr) => {
            console.log('Installed Python packages:', stdout);
        });

        const options = {
            timeout: 120000,
            maxBuffer: 1024 * 1024 * 10, // Increased buffer size
            cwd: __dirname,
            env: { 
                ...process.env,
                PYTHONPATH: `${process.env.PYTHONPATH || __dirname}:/usr/local/lib/python3.11/site-packages`,
                PYTHONUNBUFFERED: "1"
            }
        };

        exec(`${pythonPath} ${scriptPath}`, options, (error, stdout, stderr) => {
            if (error) {
                console.error('Execution error:', error);
                console.error('Error code:', error.code);
                console.error('Error signal:', error.signal);
                return;
            }
            
            if (stderr) {
                console.error('Python stderr:', stderr);
            }
            
            console.log('Python stdout:', stdout);
            
            try {
                if (fs.existsSync(jsonPath)) {
                    const weatherData = JSON.parse(fs.readFileSync(jsonPath, 'utf8'));
                    console.log('Weather data loaded successfully');
                } else {
                    console.error('Weather data file not found at:', jsonPath);
                }
            } catch (err) {
                console.error('Error reading/parsing weather data:', err);
            }
        });
    });
}

// Call this function once a day, or on demand

fetchWeatherData()




cron.schedule('00 00 * * *', () => {
    console.log('Fetching daily weather data...');
    fetchWeatherData();
});