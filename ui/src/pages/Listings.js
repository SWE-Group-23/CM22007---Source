import { Link } from "react-router-dom";
import { useState, useEffect } from "react";
import Fuse from "fuse.js";

// config for user study
const CONFIG = {
  USE_SEARCH: true,
  USE_FILTERS: true,
};

function Listings({ username }) {
  const [userLocation, setUserLocation] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [listingsWithDistance, setListingsWithDistance] = useState([]);
  const [initialListings, setInitialListings] = useState([]);
  const [maxDistance, setMaxDistance] = useState(10); // default max distance
  const [selectedTags, setSelectedTags] = useState([]);
  const [allTags, setAllTags] = useState([]);

  // load listings and generate random locations
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

  // extract unique tags from listings
  useEffect(() => {
    if (initialListings.length > 0) {
      const tags = [...new Set(initialListings.flatMap((l) => l.tags))].sort();
      setAllTags(tags);
    }
  }, [initialListings]);

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

  // update listings with distances
  useEffect(() => {
    if (userLocation) {
      const updated = initialListings.map((listing) => ({
        ...listing,
        distance: calculateDistance(
          userLocation.lat,
          userLocation.lon,
          listing.lat,
          listing.lon,
        ),
      }));
      setListingsWithDistance(updated);
    }
  }, [userLocation, initialListings]);

  let finalListings = listingsWithDistance;

  // apply search
  if (CONFIG.USE_SEARCH && searchQuery) {
    const fuse = new Fuse(finalListings, {
      keys: ["title", "description", "tags"],
      threshold: 0.4,
      findAllMatches: true,
    });
    finalListings = fuse.search(searchQuery).map((r) => r.item);
  }

  // apply filters
  if (CONFIG.USE_FILTERS) {
    finalListings = finalListings.filter((listing) => {
      const withinDistance = listing.distance <= maxDistance;
      const hasTags =
        selectedTags.length === 0 ||
        listing.tags.some((tag) => selectedTags.includes(tag));
      return withinDistance && hasTags;
    });
  }

  const handleTagToggle = (tag) => {
    if (selectedTags.includes(tag)) {
      setSelectedTags(selectedTags.filter((t) => t !== tag));
    } else {
      setSelectedTags([...selectedTags, tag]);
    }
  };

  return (
    <div className="listings-page">
      {/* Sidebar with search and filters */}
      <div className="listings-sidebar">
        <h2>Find Food</h2>

        {/* Search */}
        {CONFIG.USE_SEARCH && (
          <div className="filter-section">
            <h3>Search</h3>
            <input
              type="text"
              placeholder="Search listings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
            />
          </div>
        )}

        {/* Filters */}
        {CONFIG.USE_FILTERS && (
          <div className="filters">
            <div className="filter-section">
              <h3>Distance</h3>
              <div className="distance-filter">
                <label>Max Distance: {maxDistance} km</label>
                <input
                  type="range"
                  min="0"
                  max="20"
                  value={maxDistance}
                  onChange={(e) => setMaxDistance(Number(e.target.value))}
                />
              </div>
            </div>

            <div className="filter-section">
              <h3>Filter by Tags</h3>
              <div className="tag-filter">
                {allTags.map((tag) => (
                  <label
                    key={tag}
                    className={
                      "tag-label" +
                      (selectedTags.includes(tag) ? " selected" : "")
                    }
                  >
                    <input
                      type="checkbox"
                      checked={selectedTags.includes(tag)}
                      onChange={() => handleTagToggle(tag)}
                    />
                    {tag}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* Listings content */}
      <div className="listings-content">
        <div className="listings-grid">
          {finalListings.length > 0 ? (
            finalListings.map((listing) => (
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
                  {listing.distance !== undefined
                    ? `${listing.distance.toFixed(1)} km away`
                    : "Distance unavailable"}
                </p>
              </Link>
            ))
          ) : (
            <div className="no-results">
              <p>
                No listings match your search criteria. Try adjusting your
                filters or search terms.
              </p>
            </div>
          )}
        </div>
      </div>
    </div>
  );
}

export default Listings;
