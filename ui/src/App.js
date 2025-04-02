import "leaflet/dist/leaflet.css";
import "./App.css";
import NavBar from "./components/NavBar";
import ListingDetail from "./components/ListingDetail";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";
import { useState, useEffect } from "react";

import RequireLogin from "./RequireLogin";

import Profile from "./Profile";
import Home from "./Home";
import Listings from "./Listings";
import Pantry from "./Pantry";
import Register from "./Register";
import Login from "./Login";

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

  useEffect(() => {
    const checkLoginStatus = async () => {
      try {
        const response = await fetch("http://localhost:8080/check-logged-in", {
          credentials: "include",
        });

        if (response.ok) {
          const data = await response.json();
          setLoggedIn(data["logged-in"]);
        }
      } catch (error) {
        console.error("Error checking login status:", error);
        setLoggedIn(false);
      }
    };

    checkLoginStatus();
  }, []);

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
            element={<RequireLogin page={<Pantry />} loggedIn={loggedIn} />}
          />
          <Route
            path="/listings"
            element={<RequireLogin page={<Listings />} loggedIn={loggedIn} />}
          />
          <Route
            path="/listings/:id"
            element={
              <RequireLogin page={<ListingDetail />} loggedIn={loggedIn} />
            }
          />
          <Route
            path="/profile"
            element={<RequireLogin page={<Profile />} loggedIn={loggedIn} />}
          />
          <Route path="/login" element={<Login setLoggedIn={setLoggedIn} />} />
          <Route
            path="/register"
            element={<Register setLoggedIn={setLoggedIn} />}
          />
        </Routes>
      </main>
    </Router>
  );
}

export default App;
