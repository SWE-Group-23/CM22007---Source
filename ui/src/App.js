import "leaflet/dist/leaflet.css";
import "./App.css";
import NavBar from "./components/NavBar";
import ListingDetail from "./components/ListingDetail";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import { useState, useMemo } from "react";

import RequireLogin from "./RequireLogin";

import Profile from "./Profile";
import Home from "./Home";
import Listings from "./Listings";
import Pantry from "./Pantry";
import Register from "./Register"


const loggedOutLinks = [
    {title: "Login", path: "/login"},
    {title: "Register", path: "/register"},
]

const loggedInLinks = [
  {title: "Pantry", path: "/pantry"},
  {title: "Listings", path: "/listings"},
  {title: "Profile", path: "/profile"},
]


function App() {

  const [loggedIn, setLoggedIn] = useState(false)
  
  useMemo(() => {
    fetch("http://localhost:8080/check-logged-in", {
      credentials: "include",
    }).then(response => {
      if (response.ok) {
        response.json().then(json => {
          setLoggedIn(json.logged_in);
        })
      }
    })
  }, [setLoggedIn]);


  return (
    <Router>
      <NavBar links={loggedIn ? loggedInLinks : loggedOutLinks} />
      <main>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/pantry" element={
          <RequireLogin page={<Pantry />}
            loggedIn={loggedIn} setLoggedIn={setLoggedIn}
          />
        } />
        <Route path="/listings" element={
          <RequireLogin page={<Listings />}
            loggedIn={loggedIn} setLoggedIn={setLoggedIn}
          />
        } />
        <Route path="/listings/:id" element={
          <RequireLogin page={<ListingDetail />}
            loggedIn={loggedIn} setLoggedIn={setLoggedIn}
          />
        } />
        <Route path="/profile" element={
          <RequireLogin page={<Profile />}
            loggedIn={loggedIn} setLoggedIn={setLoggedIn}
          />
        } />
        <Route path="/login" element={
          <RequireLogin page={<Navigate to="/pantry" />}
            loggedIn={loggedIn} setLoggedIn={setLoggedIn}
          />
        } />
        <Route path="/register" element={<Register setLoggedIn={setLoggedIn} />} />
      </Routes>
      </main>
    </Router>
  );
}

export default App;
