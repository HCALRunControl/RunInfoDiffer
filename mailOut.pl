#!/usr/bin/perl -w

use Net::SMTP;

my $ServerName = "cernmx.cern.ch";

my $RealNameFrom = "hcalpro via";

my $MailFrom = "noreply\@cern.ch";

my $RealNameTo = "HCAL Expert";

my $MailTo = "$ARGV[0]\@brown.edu";

my $MailSubject = "$ARGV[1]";

#print "I would mail $MailTo\n";
#exit(1);

$smtp = Net::SMTP->new($ServerName);

die "Couldn't connect to server" unless $smtp;

$smtp->mail( $MailFrom );
$smtp->to( $MailTo );

$smtp->data();

$smtp->datasend("To: $RealNameTo <$MailTo>\n");
$smtp->datasend("From: $RealNameFrom <$MailFrom>\n");
$smtp->datasend("Subject: $MailSubject\n\n");

$line=$ARGV[2];
$smtp->datasend("$line");

$smtp->dataend();

$smtp->quit();
