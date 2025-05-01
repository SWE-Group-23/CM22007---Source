import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Fuse from "fuse.js";

function Listings({ username }) {
  const [userLocation, setUserLocation] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [listingsWithDistance, setListingsWithDistance] = useState([]);

  const [initialListings] = useState(() => [
    {
      id: 1,
      title: "Bananas",
      tags: ["fruit", "sweet"],
      image: "/img/bananas.jpg",
      distance: Math.random().toFixed(1),
      description: "A bunch of ripe bananas, only bought recently.",
      lat: 51.3766938,
      lon: -2.3234206,
      listerUsername: username,
      listerImage: "/img/blank.png",
    },
    {
      id: 2,
      title: "Bread",
      tags: ["bread", "savoury", "bakery"],
      image: "/img/bread.jpg",
      distance: Math.random().toFixed(1),
      description: "Baked too much bread, so giving some away!",
      lat: 51.3766938,
      lon: -2.3234206,
      listerUsername: "oh-yeast",
      listerImage: "/img/blank.png",
    },
    {
      id: 3,
      title: "Potatoes",
      image: "/img/potato.jpg",
      tags: ["vegetables", "savoury"],
      distance: Math.random().toFixed(1),
      description: "Spare potatoes I won't use.",
      lat: 51.3766938,
      lon: -2.3234206,
      listerUsername: "cool-guy99",
      listerImage: "/img/blank.png",
    },
    {
      id: 4,
      title: "Tomatoes",
      image: "/img/tomato.jpg",
      tags: ["fruit", "vegetables"],
      distance: Math.random().toFixed(1),
      description: "Tomatoes, bought too many for making pico de gallo.",
      lat: 51.3766938,
      lon: -2.3234206,
      listerUsername: "TomatoMagic23",
      listerImage: "/img/blank.png",
    },
  ]);

  // this would get actual location but for now just placeholder
  useEffect(() => {
    setUserLocation({
      lat: 51.369837,
      lon: -2.3655009,
    });
  }, [initialListings]);

  const calculateDistance = (lat1, lon1, lat2, lon2) => {
    const R = 6371; // earth radius in km
    const dLat = (lat2 - lat1) * (Math.PI / 180);
    const dLon = (lon2 - lon1) * (Math.PI / 180);
    const a =
      Math.sin(dLat / 2) * Math.sin(dLat / 2) +
      Math.cos(lat1 * (Math.PI / 180)) *
        Math.cos(lat2 * (Math.PI / 180)) *
        Math.sin(dLon / 2) *
        Math.sin(dLon / 2);
    const c = 2 * Math.atan2(Math.sqrt(a), Math.sqrt(1 - a));
    return R * c;
  };

  useEffect(() => {
    if (userLocation) {
      const updated = initialListings.map((listing) => ({
        ...listing,
        distance: calculateDistance(
          userLocation.lat,
          userLocation.lon,
          listing.lat,
          listing.lon,
        ).toFixed(1),
      }));
      setListingsWithDistance(updated);
    }
  }, [userLocation, initialListings]);

  const fuse = new Fuse(listingsWithDistance, {
    keys: ["title", "description", "tags"],
    threshold: 0.3,
    shouldSort: true,
  });

  const finalListings = searchQuery
    ? fuse.search(searchQuery).map((r) => r.item)
    : listingsWithDistance;

  return (
    <div className="listings-page">
      <input
        type="text"
        placeholder="Search listings..."
        value={searchQuery}
        onChange={(e) => setSearchQuery(e.target.value)}
      />

      <div className="listings-grid">
        {finalListings.map((listing) => (
          <Link
            key={listing.id}
            to={`/listings/${listing.id}`}
            state={{ listing }}
            className="listing-card"
          >
            <img
              src={listing.image}
              alt={listing.title}
              className="listing-image"
            />
            <h3 className="listing-title">{listing.title}</h3>
            <p className="listing-distance">
              {listing.distance
                ? `${listing.distance} km away`
                : "Distance unavailable"}
            </p>
          </Link>
        ))}
      </div>
    </div>
  );
}

export default Listings;
