import { useEffect } from "react";
import L from "leaflet";
import "leaflet/dist/leaflet.css"
import "./App.css";
import NavBar from "./components/NavBar";
import { BrowserRouter as Router, Route, Routes } from "react-router-dom";

function Home() {
  return (<div className="title-page">
    <div className="title-box">OpenPantry</div>
    <div className="title-text">
Save food, save money.
    </div>
  </div>);
}

function Listings() {
    // useEffect(() => {
    //     const lat = 51.3766938;
    //     const lon = -2.3234206;
    //
    //     const map = L.map("map").setView([lat, lon], 13);
    //
    //     L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
    //         attribution:
    //         '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    //     }).addTo(map);
    //
    //     L.marker([lat, lon])
    //         .addTo(map)
    //         .bindPopup("<b>Location:</b><br>University of Bath, North Road, Claverton Down, Bath, BA2 6HW")
    //         .openPopup();
    // }, [])
    //
    // return <div className="listings-page">
    //     <div id="map"/>
    //     </div>
    

    const listings = [
        {
            id: 1,
            title: "Bananas",
            image: "bananas.jpg",
            distance: (Math.random() * 10).toFixed(1),
        },
        {
            id: 2,
            title: "Bread",
            image: "bread.jpg",
            distance: (Math.random() * 10).toFixed(1),
        },
        {
            id: 3,
            title: "Potatoes",
            image: "potato.jpg",
            distance: (Math.random() * 10).toFixed(1),
        },
        {
            id: 4,
            title: "Tomatoes",
            image: "tomato.jpg",
            distance: (Math.random() * 10).toFixed(1),
        },
    ];

    return (
        <div className="listings-page">
            <div className="listings-grid">
                {listings.map((listing) => (
                    <div key={listing.id} className="listing-card">
                        <img src={listing.image} alt={listing.title} className="listing-image"/>
                        <h3 className="listing-title">{listing.title}</h3>
                        <p className="listing-distance">{listing.distance} mi away</p>
                    </div>
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
            <button className="save-btn">Save changes</button>
        </div>
        </div>
}

function App() {
  return (
    <Router>
      <NavBar />
      <Routes>
        <Route path="/" element={<Home />} />
        <Route path="/listings" element={<Listings />} />
        <Route path="/profile" element={<Profile />} />
      </Routes>
    </Router>
  );
}

export default App;
