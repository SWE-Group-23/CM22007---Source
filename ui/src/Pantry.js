import { useState } from "react";

import Food from "./components/Food";

function Pantry() {
  
  const [addingFood, setAddingFood] = useState(false);

  const [foodItems, setFoodItems] = useState([
    {name: "Banana", exp: "12/4/25", desc: "Quite yellow"},
    {name: "Ham Sandwitch", exp: "7/4/25", desc: "White bread, buttered"},
    {name: "Yoghurt", exp: "14/4/25", desc: "Strawberry Flavoured"},
  ]);

  let content;

  function addFood(formData) {
    if (addingFood) {
      setFoodItems([
        ...foodItems,
        {
          name: formData.get("name"),
          exp: formData.get("expiry"),
          desc: formData.get("description")
        }
      ]);
        setAddingFood(false);
    }
  }

  if (!addingFood) {
      content = (
        <div className="profile-page">
          <h1 className="title">Your Pantry</h1>
          <div className="food-items">
          {foodItems.map(foodItem => {
              return <Food foodItem={foodItem} />
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

