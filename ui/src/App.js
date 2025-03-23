import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css"
import "./App.css";
import NavBar from "./components/NavBar";
import ListingDetail from "./components/ListingDetail"
import { BrowserRouter as Router, Route, Routes, Link } from "react-router-dom";

function Home() {
  return (<div className="title-page">
    <div className="title-box">OpenPantry</div>
    <div className="title-text">
Save food, save money.
    </div>
  </div>);
}

function Listings() {
    const listings = [
        {
            id: 1,
            title: "Bananas",
            image: "/bananas.jpg",
            distance: (Math.random()).toFixed(1),
            description: "A bunch of ripe bananas, only bought recently.",
            lat: 51.3766938,
            lon: -2.3234206,
            listerUsername: "bananas-for-bananas",
            listerImage: "/blank.png"
        },
        {
            id: 2,
            title: "Bread",
            image: "/bread.jpg",
            distance: (Math.random()).toFixed(1),
            description: "Baked too much bread, so giving some away!",
            lat: 51.3766938,
            lon: -2.3234206,
            listerUsername: "oh-yeast",
            listerImage: "/blank.png"
        },
        {
            id: 3,
            title: "Potatoes",
            image: "/potato.jpg",
            distance: (Math.random()).toFixed(1),
            description: "Spare potatoes I won't use.",
            lat: 51.3766938,
            lon: -2.3234206,
            listerUsername: "cool-guy99",
            listerImage: "/blank.png"
        },
        {
            id: 4,
            title: "Tomatoes",
            image: "/tomato.jpg",
            distance: (Math.random()).toFixed(1),
            description: "Tomatoes, bought too many for making pico de gallo.",
            lat: 51.3766938,
            lon: -2.3234206,
            listerUsername: "TomatoMagic23",
            listerImage: "/blank.png"
        },
    ];

    return (
        <div className="listings-page">
            <div className="listings-grid">
                {listings.map((listing) => (
                    <Link key={listing.id} to={`/listings/${listing.id}`} state={{ listing }} className="listing-card">
                        <img src={listing.image} alt={listing.title} className="listing-image"/>
                        <h3 className="listing-title">{listing.title}</h3>
                        <p className="listing-distance">{listing.distance} mi away</p>
                    </Link>
                ))}
            </div>
        </div>
    )


}

function Profile() {
  return <div className="profile-page">
        <img className="profile-image" src="blank.png" alt="A dark grey silhouette on a light grey background." />
        <p className="profile-name">random-user654</p>
        <div className="profile-container">
            <label htmlFor="profile-bio" className="profile-label">Biography</label>
            <textarea type="text" className="profile-textarea" id="profile-bio" placeholder="Edit your biography..."/>
            <label htmlFor="profile-pref" className="profile-label">Dietary Requirements</label>
            <input type="text" className="profile-input" id="profile-pref" placeholder="Enter your dietary requirements..."/>
            <button className="profile-save-btn">Save changes</button>
        </div>
        </div>
}

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
