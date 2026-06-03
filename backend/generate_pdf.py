from reportlab.pdfgen import canvas

c = canvas.Canvas('test_resume.pdf')
c.drawString(100, 750, 'John Doe Resume')
c.drawString(100, 730, 'Software Engineer')
c.drawString(100, 710, 'Experience: 5 years in Python and FastAPI')
c.save()
