import streamlit as st
import pandas as pd
from datetime import datetime
import openpyxl

# Page configuration
st.set_page_config(
    page_title="Kitchen Ordering System",
    page_icon="🍽️",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# Custom CSS for mobile-friendly design
st.markdown("""
<style>
    .stButton>button {
        width: 100%;
        background-color: #2563eb;
        color: white;
        border-radius: 8px;
        padding: 0.5rem;
        font-weight: bold;
    }
    .stButton>button:hover {
        background-color: #1e40af;
    }
    .item-card {
        background-color: white;
        padding: 1rem;
        border-radius: 8px;
        border: 1px solid #e5e7eb;
        margin-bottom: 0.5rem;
    }
    .category-badge {
        background-color: #dbeafe;
        color: #1e40af;
        padding: 0.25rem 0.75rem;
        border-radius: 1rem;
        font-size: 0.875rem;
        display: inline-block;
    }
    .price-tag {
        color: #2563eb;
        font-size: 1.25rem;
        font-weight: bold;
    }
    .total-box {
        background-color: #dbeafe;
        padding: 1rem;
        border-radius: 8px;
        margin-top: 1rem;
    }
</style>
""", unsafe_allow_html=True)

# Initialize session state
if 'cart' not in st.session_state:
    st.session_state.cart = {}
if 'order_history' not in st.session_state:
    st.session_state.order_history = []
if 'inventory' not in st.session_state:
    st.session_state.inventory = None


# Function to load Excel file
def load_excel_data(uploaded_file):
    """Load and parse the Excel file with 4 sheets"""
    all_items = []
    item_id = 1

    try:
        # ✅ Read all sheets dynamically from uploaded file
        excel_file = pd.ExcelFile(uploaded_file)

        for sheet_name in excel_file.sheet_names:
            df = pd.read_excel(excel_file, sheet_name=sheet_name, header=None)

            # Start from row 2 (index 2)
            for idx in range(2, len(df)):
                row = df.iloc[idx]

                # Each row has 3 sets of items (columns 0-2, 4-6, 8-10)
                item_sets = [
                    {'name': 0, 'spec': 1, 'price': 2},
                    {'name': 4, 'spec': 5, 'price': 6},
                    {'name': 8, 'spec': 9, 'price': 10}
                ]

                for item_set in item_sets:
                    try:
                        name = row[item_set['name']]
                        spec = row[item_set['spec']]
                        price_str = row[item_set['price']]

                        if pd.isna(name) or str(name).strip() == '':
                            continue

                        # Extract price using regex
                        import re
                        price_match = re.search(r'[\d.]+', str(price_str))
                        price = float(price_match.group()) if price_match else 0

                        all_items.append({
                            'id': item_id,
                            'name': str(name).strip(),
                            'category': sheet_name,
                            'unit': str(spec).strip() if not pd.isna(spec) else '',
                            'price': price
                        })
                        item_id += 1
                    except:
                        continue

        return pd.DataFrame(all_items)
    except Exception as e:
        st.error(f"Error loading Excel file: {e}")
        return None

# Function to add item to cart
def add_to_cart(item_id, item_name, price, unit):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['quantity'] += 1
    else:
        st.session_state.cart[item_id] = {
            'name': item_name,
            'price': price,
            'unit': unit,
            'quantity': 1
        }


# Function to update quantity
def update_quantity(item_id, change):
    if item_id in st.session_state.cart:
        st.session_state.cart[item_id]['quantity'] += change
        if st.session_state.cart[item_id]['quantity'] <= 0:
            del st.session_state.cart[item_id]


# Function to calculate cart total
def calculate_total():
    total = 0
    for item in st.session_state.cart.values():
        total += item['price'] * item['quantity']
    return total


# Function to complete order
def complete_order():
    if st.session_state.cart:
        order = {
            'date': datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
            'items': dict(st.session_state.cart),
            'total': calculate_total()
        }
        st.session_state.order_history.append(order)
        st.session_state.cart = {}
        return True
    return False


# Load inventory on first run
if st.session_state.inventory is None:
    # Try to load the uploaded Excel file
    st.title("🍽️ Kitchen Ordering System")
    st.subheader("Upload Your Excel File")

    uploaded_file = st.file_uploader(
        "Upload 'JVC 规格品类.xls' file",
        type=['xls', 'xlsx']
    )

    if uploaded_file is not None:
        with st.spinner("Loading inventory..."):
            st.session_state.inventory = load_excel_data(uploaded_file)
        if st.session_state.inventory is not None:
            st.success(f"✅ Loaded {len(st.session_state.inventory)} items!")
            st.rerun()

    st.info("👆 Please upload your Excel file to start ordering")
    st.stop()

# Main App
inventory = st.session_state.inventory

# Header
st.title("🍽️ Kitchen Ordering System")
st.markdown("**JVC Staff Kitchen Materials**")

# Navigation
page = st.radio(
    "Navigation",
    ["🏠 Browse Items", "🛒 Cart", "📜 Order History"],
    horizontal=True,
    label_visibility="collapsed"
)

# Page 1: Browse Items
if page == "🏠 Browse Items":
    st.subheader("Browse Items")

    # Search and filter
    col1, col2 = st.columns([2, 1])
    with col1:
        search_query = st.text_input("🔍 Search items", "")
    with col2:
        categories = ['All'] + sorted(inventory['category'].unique().tolist())
        selected_category = st.selectbox("Category", categories)

    # Filter inventory
    filtered_df = inventory.copy()
    if search_query:
        filtered_df = filtered_df[
            filtered_df['name'].str.contains(search_query, case=False, na=False)
        ]
    if selected_category != 'All':
        filtered_df = filtered_df[filtered_df['category'] == selected_category]

    st.markdown(f"**{len(filtered_df)} items found**")

    # Display items
    for idx, row in filtered_df.iterrows():
        col1, col2 = st.columns([3, 1])

        with col1:
            st.markdown(f"**{row['name']}**")
            st.markdown(f"<span class='category-badge'>{row['category']}</span> • {row['unit']}",
                        unsafe_allow_html=True)
            st.markdown(f"<span class='price-tag'>{row['price']:.2f} AED</span>", unsafe_allow_html=True)

        with col2:
            if row['id'] in st.session_state.cart:
                qty = st.session_state.cart[row['id']]['quantity']
                st.markdown(f"**In cart: {qty}**")
                if st.button("➕", key=f"add_{row['id']}"):
                    add_to_cart(row['id'], row['name'], row['price'], row['unit'])
                    st.rerun()
            else:
                if st.button("Add to Cart", key=f"add_{row['id']}"):
                    add_to_cart(row['id'], row['name'], row['price'], row['unit'])
                    st.rerun()

        st.divider()

    # Cart summary at bottom
    if st.session_state.cart:
        cart_count = sum(item['quantity'] for item in st.session_state.cart.values())
        st.markdown(f"### 🛒 Cart: {cart_count} items - {calculate_total():.2f} AED")

# Page 2: Cart
elif page == "🛒 Cart":
    st.subheader("Your Order")

    if not st.session_state.cart:
        st.info("Your cart is empty. Add items from the Browse page!")
    else:
        # Display cart items
        for item_id, item in st.session_state.cart.items():
            col1, col2, col3 = st.columns([3, 2, 1])

            with col1:
                st.markdown(f"**{item['name']}**")
                st.markdown(f"{item['price']:.2f} AED × {item['quantity']} {item['unit']}")

            with col2:
                col_a, col_b, col_c = st.columns(3)
                with col_a:
                    if st.button("➖", key=f"dec_{item_id}"):
                        update_quantity(item_id, -1)
                        st.rerun()
                with col_b:
                    st.markdown(f"**{item['quantity']}**")
                with col_c:
                    if st.button("➕", key=f"inc_{item_id}"):
                        update_quantity(item_id, 1)
                        st.rerun()

            with col3:
                st.markdown(f"**{item['price'] * item['quantity']:.2f} AED**")
                if st.button("🗑️", key=f"del_{item_id}"):
                    del st.session_state.cart[item_id]
                    st.rerun()

            st.divider()

        # Order summary
        st.markdown("### Order Summary")
        total_items = sum(item['quantity'] for item in st.session_state.cart.values())
        total_price = calculate_total()

        st.markdown(f"**Subtotal ({total_items} items):** {total_price:.2f} AED")
        st.markdown(f"### **Total: {total_price:.2f} AED**")

        # Complete order button
        if st.button("✅ Complete Order", type="primary"):
            if complete_order():
                st.success("Order placed successfully!")
                st.balloons()
                st.rerun()

# Page 3: Order History
elif page == "📜 Order History":
    st.subheader("Order History")

    if not st.session_state.order_history:
        st.info("No orders yet. Place your first order!")
    else:
        for idx, order in enumerate(reversed(st.session_state.order_history)):
            with st.expander(
                    f"Order #{len(st.session_state.order_history) - idx} - {order['date']} - {order['total']:.2f} AED"):
                for item in order['items'].values():
                    col1, col2 = st.columns([3, 1])
                    with col1:
                        st.markdown(f"**{item['name']}** × {item['quantity']}")
                    with col2:
                        st.markdown(f"{item['price'] * item['quantity']:.2f} AED")
                st.divider()
                st.markdown(f"### Total: {order['total']:.2f} AED")

# Footer
st.markdown("---")
st.markdown("**Need help?** Contact your system administrator")