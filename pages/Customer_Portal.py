import streamlit as st
import stripe

stripe.api_key = st.secrets.stripe_api_key

st.set_page_config(
    page_title = "Customer Portal",
    page_icon = "🧠",
)

def main():
    st.title('Customer Portal')
    
    # Ask the user for their email used during the payment
    email = st.text_input('Please enter the email address used during payment:')
    
    if email:
        # Retrieve Stripe Customer ID using Stripe API by searching for customers with email
        customers = stripe.Customer.list(email=email).data

        # If there are no customers with that email, show a warning.
        if len(customers) == 0:
            st.error('No customer found with the provided email. Please check the email and try again, or contact support.')
        else:
            # Assuming the first customer returned is the one we're looking for
            customer_id = customers[0].id

            # Create a billing portal session
            session = stripe.billing_portal.Session.create(
                customer=customer_id,
                return_url=st.secrets["redirect_url"]
            )
            
            # Provide a link to the billing portal
            st.markdown(f"You can manage your billing information [here]({session.url}).", unsafe_allow_html=True)
    else:
        st.warning("Please enter the email address to proceed.")

    st.write("""\n
        ### What You Can Do:

        **Manage Your Plan:**
        - View and modify your subscription plan.
        - Upgrade, downgrade, or cancel your subscription.

        **Modify Your Account Information:**
        - Update your name, email, and the method of payment.\n
        """)
    st.error("If your payment was made with a non-Google account, please update to a Google account through the portal to use the app.")
# Run the customer portal function if this file is executed.
if __name__ == "__main__":
    main()