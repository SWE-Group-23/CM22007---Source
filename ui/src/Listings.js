import { Link } from "react-router-dom";

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

export default Listings;
