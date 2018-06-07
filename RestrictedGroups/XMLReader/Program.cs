using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;
using System.Text.RegularExpressions;
using System.IO;

namespace XMLReader{
    class Program{
        static void Main(string[] args){
			string[] files = null; // saves directory items
			
			try {// Get list of folders in \bin\Debug\GPOBackup
				files = Directory.GetDirectories("GPOBackup");
			}catch (Exception ex){
				Console.ForegroundColor = ConsoleColor.Red;
				Console.WriteLine(ex);
				Console.ResetColor();
				// Terminate program
				Console.WriteLine("Press ENTER to close...");
				Console.ReadLine();
				Environment.Exit(2);
			}
			try {// Overwrite rg.csv in \bin\Debug\ with header row
				 //List<string> header = new List<string>() { "GPO,GroupSID,GroupName,MemberSID,MemberName" };
				File.WriteAllLines("rg.csv", new[] { "GPO,GroupSID,GroupName,MemberSID,MemberName" });
			}catch (Exception ex) {
				Console.ForegroundColor = ConsoleColor.Red;
				Console.WriteLine(ex);
				Console.ResetColor();
				// Terminate program
				Console.WriteLine("Press ENTER to close...");
				Console.ReadLine();
				Environment.Exit(32);
			}

			foreach (var file in files) {
				ParseXML($"{file}\\gpreport.xml");
			}
			
			// End program successfully
			Console.WriteLine("Press ENTER to close...");
			Console.ReadLine();
			Environment.Exit(0);
        }

		static void ParseXML(string file)
		{
			List<string> csv = new List<string>();
			List<string> grpList = new List<string>();
			List<string> nodList = new List<string>();

			XElement xml = XElement.Load(file);
			//var doc = XDocument.Parse(xml);

			string gpoName = Regex.Replace(xml.FirstNode.NextNode.ToString(), "<.*?>", String.Empty);

			if (!gpoName.Contains("ENTER GPO SUBSTRING HERE")) { return; }
			Console.ForegroundColor = ConsoleColor.Green;
			Console.WriteLine($"GPO: {gpoName}");
			Console.ResetColor();
			foreach (var el in xml.Descendants()) {

				//if (el.ToString().StartsWith("<q1:RestrictedGroups") ||
				//	el.ToString().StartsWith("<q2:RestrictedGroups") ||
				//	el.ToString().StartsWith("<q3:RestrictedGroups") ||
				//	el.ToString().StartsWith("<q4:RestrictedGroups") ||
				//	el.ToString().StartsWith("<q5:RestrictedGroups") ||
				//	el.ToString().StartsWith("<q6:RestrictedGroups")) {
				if(Regex.IsMatch(el.ToString(), "^<q.?:RestrictedGroups")) {			
					foreach (var attrib in el.Elements()) {
						string cat = Regex.Replace(attrib.Name.ToString(), "{.*?}", String.Empty);
						Console.ForegroundColor = ConsoleColor.Cyan;
						Console.WriteLine($">    Type: {cat}");
						Console.ResetColor();
						foreach (var node in attrib.Nodes()) {
							string n = Regex.Replace(node.ToString(), "<.*?>", String.Empty);
							if (cat == "GroupName") {
								if (grpList.Count() == 2) { grpList.Clear(); }
								grpList.Add(n);
								nodList.Add("");
							}
							else {
								nodList.Add(n); // CSV VARS
							}
							Console.WriteLine($">        {n}");
						}
						// APPEND TO CSV
						while(nodList.Count < 2) { nodList.Insert(0, ""); }
						while(grpList.Count < 2) { grpList.Add(""); }
						csv.Add($"{gpoName},{grpList[0]},{grpList[1]},{nodList[0]},{nodList[1]}");
						nodList.Clear();
					}
				}//foreach(var node in attrib.Nodes())
			}//foreach(var el in xml.Descendants())
			try {
				File.AppendAllLines("rg.csv", csv); // Save to \bin\Debug
			}catch (Exception ex) {
				Console.ForegroundColor = ConsoleColor.Red;
				Console.WriteLine(ex);
				Console.ResetColor();
				// Terminate program
				Console.WriteLine("Press ENTER to close...");
				Console.ReadLine();
				Environment.Exit(32);
			}
		}// ParseXML() Method
    }
}
