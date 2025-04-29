import { useEffect } from "react";
import L from "leaflet";
import { useLocation, useNavigate } from "react-router-dom";

function ListingDetail() {
  const location = useLocation();
  const navigate = useNavigate();
  const { listing } = location.state;

  useEffect(() => {
    if (!listing) return;

    // Fix leaflet marker icons
    delete L.Icon.Default.prototype._getIconUrl;
    L.Icon.Default.mergeOptions({
      iconRetinaUrl: require("leaflet/dist/images/marker-icon-2x.png"),
      iconUrl: require("leaflet/dist/images/marker-icon.png"),
      shadowUrl: require("leaflet/dist/images/marker-shadow.png"),
    });

    const map = L.map("map").setView([listing.lat, listing.lon], 13);
    L.tileLayer("https://{s}.tile.openstreetmap.org/{z}/{x}/{y}.png", {
      attribution:
        '&copy; <a href="https://www.openstreetmap.org/copyright">OpenStreetMap</a> contributors',
    }).addTo(map);

    L.marker([listing.lat, listing.lon])
      .addTo(map)
      .bindPopup(`<b>${listing.title}</b><br>${listing.description}`)
      .openPopup();

    return () => map.remove();
  }, [listing]);

  if (!listing) return <div>Listing not found</div>;

  return (
    <div className="listing-detail">
      <div className="detail-grid">
        <div className="detail-image-container">
          <img
            src={listing.image}
            alt={listing.title}
            className="detail-image"
          />
        </div>
        <div className="detail-map-container">
          <div id="map" className="detail-map"></div>
        </div>
      </div>
      <div className="detail-content">
        <h2 className="listing-title">{listing.title}</h2>
        <p className="description">{listing.description}</p>
        <div className="lister-info">
          <img src={listing.listerImage} alt="Lister" className="profile-pic" />
          <span className="username">{listing.listerUsername}</span>
        </div>
        <div className="button-group">
          <button className="contact-button" onClick={() => navigate("/chat")}>
            Contact Lister
          </button>
          <button className="save-button">Save Listing</button>
        </div>
      </div>
    </div>
  );
}

export default ListingDetail;
