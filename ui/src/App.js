import "leaflet/dist/leaflet.css";
import "./App.css";
import NavBar from "./components/NavBar";
import ListingDetail from "./components/ListingDetail";
import { BrowserRouter as Router, Route, Routes, Navigate } from "react-router-dom";
import { useState } from "react";

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

  return (
    <Router>
      <NavBar links={loggedIn ? loggedInLinks : loggedOutLinks} />
      <main>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/pantry" element={
          <RequireLogin page={<Pantry />} loggedIn={loggedIn} />
        } />
        <Route path="/listings" element={<Listings />} />
        <Route path="/listings/:id" element={<ListingDetail />} />
        <Route path="/profile" element={<Profile />} />
        <Route path="/login" element={
          <RequireLogin page={<Navigate to="/" />} loggedIn={loggedIn} />
        } />
        <Route path="/register" element={<Register setLoggedIn={setLoggedIn} />} />
      </Routes>
      </main>
    </Router>
  );
}

export default App;
