import { useState, useEffect } from "react";
import { Link } from "react-router-dom";
import Fuse from "fuse.js";

// user study configuration.
const STUDY_CONFIG = {
  methodOrder: ["search", "filter"],
  trials: {
    search: [
      { id: 1, targetId: 12, prompt: "Jasmine Rice", training: true },
      { id: 2, targetId: 99, prompt: "Edamame", training: true },
      { id: 3, targetId: 53, prompt: "Granola Bar", training: true },
      { id: 4, targetId: 51, prompt: "Frozen Pizza" },
      { id: 5, targetId: 10, prompt: "Onions" },
      { id: 6, targetId: 20, prompt: "Oranges" },
      { id: 7, targetId: 43, prompt: "Fresh Figs" },
      { id: 8, targetId: 95, prompt: "Mangoes" },
    ],
    filter: [
      { id: 9, targetId: 85, prompt: "Kiwis", training: true },
      { id: 10, targetId: 82, prompt: "Frozen Dumplings", training: true },
      { id: 11, targetId: 41, prompt: "Bell Peppers", training: true },
      { id: 12, targetId: 74, prompt: "Dill Pickles" },
      { id: 13, targetId: 19, prompt: "Sourdough Bread" },
      { id: 14, targetId: 61, prompt: "Raspberries" },
      { id: 15, targetId: 71, prompt: "Hummus" },
      { id: 16, targetId: 39, prompt: "Sweetcorn" },
    ],
  },
};

function Listings({ username }) {
  // listings state variables
  const [userLocation, setUserLocation] = useState(null);
  const [searchQuery, setSearchQuery] = useState("");
  const [listingsWithDistance, setListingsWithDistance] = useState([]);
  const [initialListings, setInitialListings] = useState([]);
  const [maxDistance, setMaxDistance] = useState(10);
  const [selectedTags, setSelectedTags] = useState([]);
  const [allTags, setAllTags] = useState([]);

  // study state variables
  const [trials, setTrials] = useState([]);
  const [currentTrialIndex, setCurrentTrialIndex] = useState(0);
  const [studyData, setStudyData] = useState([]);
  const [isTrialActive, setIsTrialActive] = useState(false);
  const [startTime, setStartTime] = useState(0);
  const [methodOrder, setMethodOrder] = useState([]);
  const [showBreakScreen, setShowBreakScreen] = useState(false);
  const [incorrectSelectionId, setIncorrectSelectionId] = useState(null);
  const [failedAttempts, setFailedAttempts] = useState(0);

  // initialize study
  useEffect(() => {
    const initializeStudy = () => {
      // select method order based on config
      const methodPairs = STUDY_CONFIG.methodOrder.map((method) => ({
        method,
        trials: STUDY_CONFIG.trials[method],
      }));

      // order the trials
      const orderedTrials = [
        ...methodPairs[0].trials.map((t) => ({
          ...t,
          method: methodPairs[0].method,
          phase: t.training ? "training" : "main",
        })),
        ...methodPairs[1].trials.map((t) => ({
          ...t,
          method: methodPairs[1].method,
          phase: t.training ? "training" : "main",
        })),
      ];

      // set up the study state
      setMethodOrder(STUDY_CONFIG.methodOrder);
      setTrials(orderedTrials);
    };

    initializeStudy();
  }, []);

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

  // calculate crow distance
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

  const startTrial = () => {
    // reset interface state
    setSearchQuery("");
    setSelectedTags([]);
    setMaxDistance(10);
    window.scrollTo(0, 0);

    // start trial
    setIsTrialActive(true);
    setStartTime(performance.now());
  };

  const handleListingClick = (e, listingId) => {
    if (!isTrialActive) return;
    e.preventDefault();

    const currentTrial = trials[currentTrialIndex];

    if (listingId !== currentTrial.targetId) {
      // flash incorrect selection and count failure
      setIncorrectSelectionId(listingId);
      setFailedAttempts((prev) => prev + 1);
      setTimeout(() => setIncorrectSelectionId(null), 500);
      return;
    }

    // handle correct selection
    const endTime = performance.now();
    const timeTaken = endTime - startTime;

    // add trial result
    const trialResult = {
      ...currentTrial,
      selectedId: listingId,
      timeTaken: timeTaken.toFixed(3),
      success: true,
      failedAttempts,
      timestamp: new Date().toISOString(),
    };

    setStudyData((prev) => [...prev, trialResult]);
    console.log("Trial result:", trialResult);

    // reset failures for next trial
    setFailedAttempts(0);

    // handle trial progression
    const isLastTrial = currentTrialIndex === trials.length - 1;
    const isMethodSwitch = currentTrialIndex === 7;

    // while not the last trial
    if (!isLastTrial) {
      // if we have to switch methods
      if (isMethodSwitch) {
        // show the break screen
        setShowBreakScreen(true);
      } else {
        // otherwise increment trial index
        setCurrentTrialIndex((prev) => prev + 1);
      }
    } else {
      // if on the last trial, increment index anyways
      setCurrentTrialIndex((prev) => prev + 1);
    }

    // deactivate trial
    setIsTrialActive(false);
  };

  // continue on from a break
  const handleBreakContinue = () => {
    setShowBreakScreen(false);
    setCurrentTrialIndex((prev) => prev + 1);
  };

  // export the trial data as json
  const exportData = () => {
    const data = {
      participant: username,
      methodOrder,
      trials: studyData,
    };

    const blob = new Blob([JSON.stringify(data, null, 2)], {
      type: "application/json",
    });
    const url = URL.createObjectURL(blob);
    const a = document.createElement("a");
    a.href = url;
    a.download = `openpantry-study-${username}-${Date.now()}.json`;
    document.body.appendChild(a);
    a.click();
    document.body.removeChild(a);
    URL.revokeObjectURL(url);
  };

  // get current trial information
  const currentTrial = trials[currentTrialIndex] || {};
  const currentMethod = currentTrial.method;
  const isSearchMethod = currentMethod === "search";
  const isFilterMethod = currentMethod === "filter";

  // filter tag toggling
  const handleTagToggle = (tag) => {
    setSelectedTags((prev) =>
      prev.includes(tag) ? prev.filter((t) => t !== tag) : [...prev, tag],
    );
  };

  // filter listings based on current method
  let filteredListings = listingsWithDistance;

  if (isSearchMethod && searchQuery) {
    const fuse = new Fuse(filteredListings, {
      keys: ["title", "description", "tags"],
      threshold: 0.4,
      findAllMatches: true,
    });
    filteredListings = fuse.search(searchQuery).map((r) => r.item);
  }

  if (isFilterMethod) {
    filteredListings = filteredListings.filter((listing) => {
      const withinDistance = listing.distance <= maxDistance;
      const hasTags =
        selectedTags.length === 0 ||
        selectedTags.every((tag) => listing.tags.includes(tag));
      return withinDistance && hasTags;
    });
  }

  return (
    <div className="listings-page">
      {/* trial overlay */}
      {((currentTrialIndex < trials.length && !isTrialActive) ||
        showBreakScreen) && (
        <div className="trial-overlay">
          <div className="trial-modal">
            {showBreakScreen ? (
              <div className="break-screen">
                <h2>Break Time</h2>
                <p>Please wait for about 1 minute before continuing</p>
                <button onClick={handleBreakContinue}>Continue</button>
              </div>
            ) : (
              <div className="trial-prompt">
                <h3>{currentTrial.prompt}</h3>
                <button onClick={startTrial} className="start-button">
                  Start Trial {currentTrialIndex + 1}
                </button>
                <p>Using {currentTrial.method} method</p>
                {currentTrial.training && <p>(Training trial)</p>}
              </div>
            )}
          </div>
        </div>
      )}

      {currentTrialIndex >= trials.length && (
        <div className="trial-overlay">
          <div className="trial-modal">
            <h2>Study Complete!</h2>
            <button onClick={exportData}>Download Study Data</button>
          </div>
        </div>
      )}

      {/* sidebar */}
      <div className="listings-sidebar">
        <h2>Find Food</h2>

        {/* search */}
        {isSearchMethod && (
          <div className="filter-section">
            <h3>Search</h3>
            <input
              type="text"
              placeholder="Search listings..."
              value={searchQuery}
              onChange={(e) => setSearchQuery(e.target.value)}
              disabled={!isTrialActive}
            />
          </div>
        )}

        {/* filters */}
        {isFilterMethod && (
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
                  disabled={!isTrialActive}
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
                      disabled={!isTrialActive}
                    />
                    {tag}
                  </label>
                ))}
              </div>
            </div>
          </div>
        )}
      </div>

      {/* listings grid */}
      <div className="listings-content">
        <div className="listings-grid">
          {filteredListings.length > 0 ? (
            filteredListings.map((listing) => (
              <Link
                key={listing.id}
                to={`/listings/${listing.id}`}
                state={{ listing }}
                className={`listing-card ${
                  incorrectSelectionId === listing.id
                    ? "incorrect-selection"
                    : ""
                }`}
                onClick={(e) => handleListingClick(e, listing.id)}
                style={{ pointerEvents: isTrialActive ? "auto" : "none" }}
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
