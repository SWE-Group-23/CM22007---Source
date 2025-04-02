import { useState } from "react";

import Food from "./components/Food";

let itemId = 0

function Pantry() {
  
  const [addingFood, setAddingFood] = useState(false);
  const [postingListing, setPostingListing] = useState(false);
  const [listingItem, setListingItem] = useState(null);

  const [foodItems, setFoodItems] = useState([
    {id: itemId++, name: "Banana", exp: "12/4/25", desc: "Quite yellow"},
    {id: itemId++, name: "Ham Sandwitch", exp: "7/4/25", desc: "White bread, buttered"},
    {id: itemId++, name: "Yoghurt", exp: "14/4/25", desc: "Strawberry Flavoured"},
  ]);

  let content;

  function addFood(formData) {
    if (addingFood) {
      setFoodItems([
        ...foodItems,
        {
          id: itemId++,
          name: formData.get("name"),
          exp: formData.get("expiry"),
          desc: formData.get("description")
        }
      ]);
        setAddingFood(false);
    }
  }

  function addListing(formData) {
      setPostingListing(false)
  }
  
  if (postingListing) {
      content = (
        <div className="page">
          <div className="form-container">
            <h1 className="title">Posting {listingItem.name}</h1>
            <form action={addListing}>
              <label htmlFor="location">Enter Location:</label>
              <input type="text" name="name" />
              <label htmlFor="details">Enter Details:</label>
              <textarea name="details" rows="4" />
              <div className="button-group">
                <input type="submit" className="dark-button" value="Post Listing" />
                <input
                  type="submit"
                  onClick={() => {setPostingListing(false)}}
                  className="light-button"
                  value="Cancel" 
                />
              </div>
            </form>
          </div>
        </div>
      );
  } else if (!addingFood) {
      content = (
        <div className="profile-page">
          <h1 className="title">Your Pantry</h1>
          <div className="food-items">
          {foodItems.map(foodItem => {
              return <Food key={foodItem.id} foodItem={foodItem}
                setPostingListing={setPostingListing} setListingItem={setListingItem}
              />
          })}
          </div>
          <button
            onClick={() => {setAddingFood(true)}}
            className="dark-button jc-center-margin"
          >
            Add Food
          </button>
        </div>
      );
  } else {
      content = (
        <div className="page">
          <div className="form-container">
            <h1 className="title">Adding Food</h1>
            <form action={addFood}>
              <label htmlFor="name">Enter Name:</label>
              <input type="text" name="name" />
              <label htmlFor="expiry">Enter Expiry:</label>
              <input type="text" name="expiry" />
              <label htmlFor="description">Enter Description:</label>
              <textarea name="description" rows="4" />
              <label htmlFor="ingredients">Enter Ingredients:</label>
              <textarea name="ingredients" rows="4" />
              <div className="button-group">
                <input type="submit" className="dark-button" value="Add Food" />
                <input
                  type="submit"
                  onClick={() => {setAddingFood(false)}}
                  className="light-button"
                  value="Cancel" 
                />
              </div>
            </form>
          </div>
        </div>
      )
  }

  return content;
}

export default Pantry;

