import streamlit as st
import stripe

stripe.api_key = st.secrets.stripe_api_key

st.set_page_config(
    page_title = "Customer Portal",
    page_icon = "🧠",
)

class User:
    def __init__(self, email, is_japanese):
        self.email = email
        self.is_japanese = is_japanese

def translate(text_japanese, text_english, is_japanese):
    return text_japanese if is_japanese else text_english

def run_stripe(user):
    # Retrieve Stripe Customer ID using Stripe API by searching for customers with email
    customers = stripe.Customer.list(email=user.email).data

    # If there are no customers with that email, show a warning.
    if len(customers) == 0:
        st.error(translate('指定されたメールアドレスの顧客が見つかりません。メールアドレスを確認して再試行するか、サポートにお問い合わせください。',
                            'No customer found with the provided email. Please check the email and try again, or contact support.', 
                            user.is_japanese))
    else:
        # Assuming the first customer returned is the one we're looking for
        customer_id = customers[0].id

        # Create a billing portal session
        session = stripe.billing_portal.Session.create(
            customer=customer_id,
            return_url=st.secrets["redirect_url"]
        )

        # Provide a link to the billing portal
        st.markdown(translate(f"請求情報は[こちら]({session.url})で管理できます。",
                              f"You can manage your billing information [here]({session.url}).", 
                              user.is_japanese),
                    unsafe_allow_html=True)

def main():
    # Language switch toggle
    JP = st.toggle("Japanese (日本語)", value=False)
    st.title(translate('カスタマーポータル', 'Customer Portal', JP))

    # Ask the user for their email used during the payment
    email = st.text_input(translate('支払い時に使用したメールアドレスを入力してください：', 
                                    'Please enter the email address used during payment:', 
                                    JP))
    if email:
        user = User(email, JP)
        run_stripe(user)
    else:
        st.warning(translate("続行するにはメールアドレスを入力してください.", 
                             "Please enter the email address to proceed.", 
                             JP))

    #explain Customer Portal
    st.write(translate("""\n
        ### できること:

        **プランの管理:**
        - サブスクリプションプランを表示および変更します。
        - サブスクリプションをアップグレード、ダウングレード、またはキャンセルします。

        **アカウント情報の変更:**
        - 名前、メールアドレス、および支払い方法の更新。\n
        """,
        """\n
        ### What You Can Do:

        **Manage Your Plan:**
        - View and modify your subscription plan.
        - Upgrade, downgrade, or cancel your subscription.

        **Modify Your Account Information:**
        - Update your name, email, and the method of payment.\n
        """, JP))

    st.error(translate("非Googleアカウントでの支払いの場合、アプリを使用するためにはメールアドレスをポータル経由でGoogleアカウントに更新してください.",
                        "If your payment was made with a non-Google account, please update to a Google account through the portal to use the app.", 
                        JP))

if __name__ == "__main__":
    main()