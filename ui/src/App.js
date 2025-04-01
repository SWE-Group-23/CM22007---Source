import "leaflet/dist/leaflet.css"
import "./App.css";
import NavBar from "./components/NavBar";
import ListingDetail from "./components/ListingDetail"
import { BrowserRouter as Router, Route, Routes} from "react-router-dom";

import Profile from "./Profile"
import Home from "./Home"
import Listings from "./Listings"


function App() {
  return (
    <Router>
      <head>
          <title>OpenPantry - Save Food, Save Money</title>
      </head>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/listings" element={<Listings />} />
        <Route path="/listings/:id" element={<ListingDetail />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Router>
  );
}

export default App;
