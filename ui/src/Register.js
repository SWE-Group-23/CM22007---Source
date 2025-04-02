import "./Register.css";

import { useState } from "react";
import { Navigate } from "react-router-dom";

import QRCode from "qrcode";

function Register({ setLoggedIn }) {
  const [registerState, setRegisterState] = useState(0);
  const [username, setUsername] = useState(null);
  let [imageSource, setImageSource] = useState(null);
  let [backupCode, setBackupCode] = useState(null);

  function submitUsername(formData) {
    fetch("http://localhost:8080/register/check-valid-username", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ username: formData.get("username") }),
    }).then((response) => {
      if (response.ok) {
        response.json().then((json) => {
          if (json.valid) {
            setUsername(formData.get("username"));
            setRegisterState(1);
          } else {
            alert("Username invalid");
          }
        });
      } else {
        alert("Unknown Error");
      }
    });
  }

  function submitPassword(formData) {
    if (formData.get("password") === formData.get("password2")) {
      fetch("http://localhost:8080/register/check-password", {
        method: "POST",
        credentials: "include",
        headers: {
          "Content-Type": "application/json",
        },
        body: JSON.stringify({
          username: username,
          password: formData.get("password"),
        }),
      }).then((response) => {
        if (response.ok) {
          response.json().then((json) => {
            fetch("http://localhost:8080/register/setup-otp", {
              credentials: "include",
            }).then((response) => {
              response.json().then((json) => {
                QRCode.toDataURL(json.prov_uri).then((url) => {
                  setImageSource(url);
                });
              });
            });
            setRegisterState(2);
          });
        } else {
          alert("Unknown Error");
        }
      });
    } else {
      alert("Password mismatch");
    }
  }

  function submitOTP(formData) {
    fetch("http://localhost:8080/register/verify-otp", {
      method: "POST",
      credentials: "include",
      headers: {
        "Content-Type": "application/json",
      },
      body: JSON.stringify({ otp: formData.get("otp") }),
    }).then((response) => {
      if (response.ok) {
        response.json().then((json) => {
          if (json.correct) {
            fetch("http://localhost:8080/register/backup-code", {
              credentials: "include",
            }).then((response) => {
              response.json().then((json) => {
                setBackupCode(json.backup_code);
              });
            });
            setRegisterState(3);
          } else {
            alert("OTP invalid");
          }
        });
      } else {
        alert("Unknown Error");
      }
    });
  }

  function login() {
    setLoggedIn(true);
    setRegisterState(4);
  }

  let content;

  switch (registerState) {
    // Enter Username
    case 0:
      content = (
        <form action={submitUsername}>
          <label htmlFor="username">Enter Username:</label>
          <input type="text" name="username" />
          <input type="submit" value="Submit" />
        </form>
      );
      break;
    // Enter Password
    case 1:
      content = (
        <form action={submitPassword}>
          <label htmlFor="password">Enter Password:</label>
          <input type="password" name="password" />
          <label htmlFor="password2">Reenter Password:</label>
          <input type="password" name="password2" />
          <input type="submit" value="Submit" />
        </form>
      );
      break;
    // Set Up OTP
    case 2:
      content = (
        <form action={submitOTP}>
          <img src={imageSource} />
          <label htmlFor="otp">Enter OTP:</label>
          <input type="password" name="otp" />
          <input type="submit" value="Submit" />
        </form>
      );
      break;
    // Get Backup Codes
    case 3:
      content = (
        <div>
          <h2>Account Registered</h2>
          <p>Backup Code: <strong>{backupCode}</strong></p>
          <p>Make sure you write your backup code down,
          print it out, or save it securely somewhere.</p>
          <button onClick={login}>Continue</button>
        </div>
      );
      break;
    // Got To Pantry
    case 4:
      content = <Navigate to="/pantry" />;
  }

  return (
    <div className="register-page">
      <div className="register-container">{content}</div>
    </div>
  );
}

export default Register;
