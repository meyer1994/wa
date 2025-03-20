from mangum import Mangum

import wa.app

# This is simply the file used to run the app in AWS
app = wa.app.create()
handler = Mangum(app)
