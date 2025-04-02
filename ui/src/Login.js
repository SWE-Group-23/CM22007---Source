import "./Register.css";

import { useState } from "react";


function Login({ setLoggedIn, setSessionUsername }) {
    
    const [registerState, setRegisterState] = useState(0);
    const [username, setUsername] = useState(null);

    function submitCreds(formData) {
        fetch("http://localhost:8080/login/check-password", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ 
                username: formData.get("username"),
                password: formData.get("password"),
            })
        }).then(response => {
            if (response.ok) {
                response.json().then(json => {
                    if (json.correct) {
                        setRegisterState(1);
                        setUsername(formData.get("username"));
                    } else {
                        alert("Creds invalid");
                    }
                })
            } else {
                alert("Unknown Error");
            }
        });
    }

    function submitOTP(formData) {
        fetch("http://localhost:8080/login/verify-otp", {
            method: "POST",
            credentials: "include",
            headers: {
                "Content-Type": "application/json",
            },
            body: JSON.stringify({ otp: formData.get("otp") })
        }).then(response => {
            if (response.ok) {
                response.json().then(json => {
                    if (json.correct) {
                        setLoggedIn(true);
                        setSessionUsername(username);
                    } else {
                        alert("OTP invalid");
                    }
                })
            } else {
                alert("Unknown Error");
            }
        });
    }

    let content;

    switch (registerState) {
        // Enter Username and Password
        case 0:
            content = (
              <form action={submitCreds}>
                <label htmlFor="username">Enter Username:</label>
                <input type="text" name="username" />
                <label htmlFor="password">Enter Password:</label>
                <input type="password" name="password" />
                <input type="submit" value="Submit" />
              </ form>
            );
            break;
        // Set Up OTP
        case 1:
            content = (
              <form action={submitOTP}>
                <label htmlFor="otp">Enter OTP:</label>
                <input type="password" name="otp" />
                <input type="submit" value="Submit" />
              </form>
            );
            break;
    }


    return (
      <div className="register-page">
        <div className="register-container">{content}</div>
      </div>
    );
}

export default Login;
