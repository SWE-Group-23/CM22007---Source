import "leaflet/dist/leaflet.css";
import "./App.css";
import NavBar from "./components/NavBar";
import ListingDetail from "./components/ListingDetail";
import {
  BrowserRouter as Router,
  Route,
  Routes,
  Navigate,
} from "react-router-dom";
import { useState, useEffect } from "react";

import RequireLogin from "./RequireLogin";

import Profile from "./Profile";
import Home from "./Home";
import Listings from "./Listings";
import Pantry from "./Pantry";
import Chat from "./Chat";
import Register from "./Register";

const loggedOutLinks = [
  { title: "Login", path: "/login" },
  { title: "Register", path: "/register" },
];

const loggedInLinks = [
  { title: "Pantry", path: "/pantry" },
  { title: "Listings", path: "/listings" },
  { title: "Profile", path: "/profile" },
];

function App() {
  const [loggedIn, setLoggedIn] = useState(null);
  const [username, setUsername] = useState("");

  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        const response = await fetch("http://localhost:8080/check-logged-in", {
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          setLoggedIn(data.logged_in);
          if (data.logged_in) {
            setUsername(data.username);
          }
        }
      } catch (error) {
        console.error("Error checking login status:", error);
        setLoggedIn(false);
      }
    };

    checkLoginStatus();
  }, [setLoggedIn]);

  if (loggedIn === null) {
    return <div>Loading...</div>;
  }

  return (
    <Router>
      <NavBar links={loggedIn ? loggedInLinks : loggedOutLinks} />
      <main>
        <Routes>
          <Route path="/" element={<Home />} />
          <Route
            path="/pantry"
            element={
              <RequireLogin
                page={<Pantry />}
                loggedIn={loggedIn}
                setLoggedIn={setLoggedIn}
              />
            }
          />
          <Route
            path="/listings"
            element={
              <RequireLogin
                page={<Listings username={username} />}
                loggedIn={loggedIn}
                setLoggedIn={setLoggedIn}
              />
            }
          />
          <Route
            path="/listings/:id"
            element={
              <RequireLogin
                page={<ListingDetail />}
                loggedIn={loggedIn}
                setLoggedIn={setLoggedIn}
              />
            }
          />
          <Route
            path="/profile"
            element={
              <RequireLogin
                page={<Profile username={username} />}
                loggedIn={loggedIn}
                setLoggedIn={setLoggedIn}
              />
            }
          />
          } />
          <Route
            path="/chat"
            element={
              <RequireLogin
                page={<Chat />}
                loggedIn={loggedIn}
                setLoggedIn={setLoggedIn}
              />
            }
          />
          <Route
            path="/login"
            element={
              <RequireLogin
                page={<Navigate to="/pantry" />}
                loggedIn={loggedIn}
                setLoggedIn={setLoggedIn}
                setSessionUsername={setUsername}
              />
            }
          />
          <Route
            path="/register"
            element={
              <Register
                setLoggedIn={setLoggedIn}
                setSessionUsername={setUsername}
              />
            }
          />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
