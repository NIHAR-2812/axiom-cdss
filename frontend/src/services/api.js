import axios from 'axios';

const API_BASE_URL = 'http://127.0.0.1:8000';
let authToken = null;

// 1. Authenticate and get JWT Token
export const login = async (username, password) => {
    const formData = new URLSearchParams();
    formData.append('username', username);
    formData.append('password', password);

    const response = await axios.post(`${API_BASE_URL}/token`, formData, {
        headers: { 'Content-Type': 'application/x-www-form-urlencoded' }
    });
    
    authToken = response.data.access_token;
    return authToken;
};

// 2. Send Symptoms to Inference Engine
export const getDiagnosis = async (symptomsArray) => {
    if (!authToken) throw new Error("Not authenticated");

    const response = await axios.post(
        `${API_BASE_URL}/api/v1/inference/predict`,
        { symptoms: symptomsArray },
        {
            headers: {
                'Authorization': `Bearer ${authToken}`,
                'Content-Type': 'application/json'
            }
        }
    );
    
    return response.data;
};