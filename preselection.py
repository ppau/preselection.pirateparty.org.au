import tornado.web
import tornado.options
import logging

from collections import OrderedDict
from tornado.web import HTTPError, RequestHandler, StaticFileHandler
from tornado.httpserver import HTTPServer
from bbqutils.email import sendmail, create_email, create_attachment

class Application(tornado.web.Application):
    def __init__(self, handlers, **settings):
        tornado.web.Application.__init__(self, handlers, **settings)

        t = open('template.html')
        self.template = t.read()
        t.close()

        t = open('success-template.html')
        self.success_template = t.read()
        t.close()

        self.email_to = "nationalcouncil@pirateparty.org.au"

class PreselectionHandler(RequestHandler):
    def get(self):
        self.write(self.application.template)

    def post(self):
        fields = OrderedDict([
            ("Candidate Details", OrderedDict([
                ("Full Name", "name"),
                ("Phone", "phone"),
                ("Email", "email")
            ])),
            ("Nomination", {"State": "nomination_state"}),
            ("Seconder Details", OrderedDict([
                ("Full Name", "seconder_name"),
                ("Phone", "seconder_phone"),
                ("Email", "seconder_email")
            ])),
            ("Candidate Questions", OrderedDict([
                ("Why do you feel that you are qualified for the position for which you have declared your candidacy?", "q1"),
                ("Why are you seeking the position for which you have declared your candidacy?", "q2"),
                ("What experience/contribution have you made so far to the Pirate movement, and what will you do to advance or better the Party and movement?", "q3"),
                ("Do you agree with the Pirate Party platform and its ideals? What other political movements or parties have you been a part of?", "q4"),
                ("# Disclosure of history", "background")
            ])),
            ("Submission", {"Pledge agreed to?": "pledge"})
        ])

        # Deal with files
        attachments = []
        for file in self.request.files.values():
            attachments.append(create_attachment(file[0]['filename'], file[0]['body']))

        answers = []
        for heading, x in fields.items():
            answers.append("\n# %s" % heading)
            for k, v in x.items():
                if heading == "Candidate Questions":
                    answers.append("%s\n%s\n" % (k, self.get_argument(v, "")))
                elif heading == "Submission":
                    answers.append("%s\n%s\n" % (k, "Yes" if self.get_argument(v, "") == "on" else "No"))
                else:
                    answers.append("%s: %s" % (k, self.get_argument(v, "")))

        name = self.get_argument("name")
        text = "\n".join(answers).strip()
        frm = "%s <%s>" % (name, self.get_argument('email'))

        sendmail(create_email(
            frm=self.application.email_to,
            to=self.application.email_to,
            subject="Preselection Nomination: %s" % name,
            text=text,
            attachments=attachments
        ))

        logging.debug(text)
        self.write(self.application.success_template % text)

if __name__ == "__main__":
    tornado.options.parse_command_line()
    application = Application([
        (r"/", PreselectionHandler),
        (r"/static/(.*)", StaticFileHandler, {"path": "static"})
    ])
    serv = HTTPServer(application, xheaders=True)
    serv.listen(12013)
    tornado.ioloop.IOLoop.instance().start()
