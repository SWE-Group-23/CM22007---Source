import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Fuse from "fuse.js";

function Listings({ username }) {
  const [userLocation, setUserLocation] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [listingsWithDistance, setListingsWithDistance] = useState([]);

  const [initialListings, setInitialListings] = useState([]);

  useEffect(() => {
    const loadListings = async () => {
      const baseLat = 51.3766938;
      const baseLon = -2.3234206;

      const response = await fetch("listings.json");
      if (!response.ok) throw new Error("Failed to load listings");
      const listings = await response.json();

      const randomiseLocation = (id) => ({
        lat: baseLat + Math.sin(id * 18) * 0.033,
        lon: baseLon + Math.cos(id * 18) * 0.033,
      });

      setInitialListings(
        listings.map((item) => ({
          ...item,
          ...randomiseLocation(item.id),
        })),
      );
    };

    loadListings();
  }, []);

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
    threshold: 0.4,
    findAllMatches: true,
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
