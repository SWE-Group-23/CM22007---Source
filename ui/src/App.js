import "leaflet/dist/leaflet.css"
import "./App.css";
import NavBar from "./components/NavBar";
import ListingDetail from "./components/ListingDetail"
import { BrowserRouter as Router, Route, Routes} from "react-router-dom";

import Profile from "./Profile"
import Home from "./Home"
import Listings from "./Listings"
import Pantry from "./Pantry"


function App() {
  return (
    <Router>
      <head>
          <title>OpenPantry - Save Food, Save Money</title>
      </head>
      <NavBar />
      <main>
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/pantry" element={<Pantry />} />
        <Route path="/listings" element={<Listings />} />
        <Route path="/listings/:id" element={<ListingDetail />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
      </main>
    </Router>
  );
}

export default App;
