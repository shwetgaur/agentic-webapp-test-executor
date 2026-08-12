# Sample plain-text test cases (Phase-1)
# Target app (public): Sauce Demo — https://www.saucedemo.com/
# These are INPUTS for the Agentic Executor (later parsed to JSON steps).

## TC01_login_success
Module: login
Owner team: auth-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Verify URL contains inventory.html
6. Verify text Products is visible

## TC02_login_invalid_password
Module: login
Owner team: auth-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with wrong_password
4. Click the Login button
5. Verify text Epic sadface is visible

## TC03_product_search_filter
Module: search
Owner team: catalog-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Verify text Products is visible
6. Select Name (Z to A) from the product sort dropdown
7. Verify text Test.allTheThings() T-Shirt (Red) is visible

## TC04_add_to_cart_flow
Module: checkout
Owner team: checkout-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Click Add to cart for Sauce Labs Backpack
6. Click the shopping cart link
7. Verify text Sauce Labs Backpack is visible
8. Verify text Your Cart is visible

## TC05_checkout_information
Module: checkout
Owner team: checkout-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Click Add to cart for Sauce Labs Bike Light
6. Click the shopping cart link
7. Click Checkout
8. Fill First Name with Ada
9. Fill Last Name with Lovelace
10. Fill Zip/Postal Code with 411001
11. Click Continue
12. Verify text Checkout: Overview is visible

## TC06_logout_navigation
Module: navigation
Owner team: catalog-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Click the menu button
6. Click Logout
7. Verify URL is https://www.saucedemo.com/
8. Verify text Swag Labs is visible OR Login button is visible

## TC07_locked_out_user
Module: login
Owner team: auth-frontend
1. Open https://www.saucedemo.com/
2. Fill username with locked_out_user
3. Fill password with secret_sauce
4. Click the Login button
5. Verify text locked out is visible

## TC08_form_validation_checkout_empty
Module: form
Owner team: catalog-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Click Add to cart for Sauce Labs Onesie
6. Click the shopping cart link
7. Click Checkout
8. Click Continue without filling fields
9. Verify text Error is visible OR First Name is required is visible

## TC09_remove_from_cart
Module: checkout
Owner team: checkout-frontend
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Click Add to cart for Sauce Labs Fleece Jacket
6. Click the shopping cart link
7. Verify text Sauce Labs Fleece Jacket is visible
8. Click Remove
9. Verify text Sauce Labs Fleece Jacket is not required to remain visible after remove

## TC10_intentional_fail_for_notify_demo
Module: validation
Owner team: qa-platform
Purpose: Intentionally fail to demonstrate pass/fail report + scrum notify agent
1. Open https://www.saucedemo.com/
2. Fill username with standard_user
3. Fill password with secret_sauce
4. Click the Login button
5. Verify text THIS_TEXT_DOES_NOT_EXIST_ON_PAGE is visible
