using System;
using System.Collections.Generic;
using System.Linq;
using System.Text;
using System.Threading.Tasks;
using System.Xml.Linq;
using System.Text.RegularExpressions;
using System.IO;

namespace GPOReader
{
	class Program
	{
		static void Main(string[] args)
		{
			string[] files = null; // saves directory items

			try {// Get list of folders in \bin\Debug\GPOBackup
				files = Directory.GetDirectories("GPOBackup");
			}
			catch (Exception ex) {
				Console.ForegroundColor = ConsoleColor.Red;
				Console.WriteLine(ex);
				Console.ResetColor();
				// Terminate program
				Console.WriteLine("Press ENTER to close...");
				Console.ReadLine();
				Environment.Exit(2);
			}
			try {// Overwrite ilt.csv in \bin\Debug\ with header row
				File.WriteAllLines("ilt.csv", new[] { "GPO,Drive,Path,Label,FilterType,FilterSID,FilterName" });
			}
			catch (Exception ex) {
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
			List<Entry> entries = new List<Entry>();
			Entry ent = new Entry();
			XElement xml = XElement.Load(file);

			string gpoName = Regex.Replace(xml.FirstNode.NextNode.ToString(), "<.*?>", String.Empty);
			ent.GPO = gpoName; // UPDATE ENTRY -- GPO
			if (!gpoName.Contains("ENTER GPO SUBSTRING HERE")) { return; }

			Console.ForegroundColor = ConsoleColor.Green;
			Console.WriteLine($"GPO: {gpoName}");
			Console.ResetColor();

			foreach (var el in xml.Descendants()) {
				if (Regex.IsMatch(el.ToString(), "^<q.{0,2}:DriveMapSettings")) {
					foreach (var attrib in el.Elements()) {
						string cat = Regex.Replace(attrib.Name.ToString(), "{.*?}", String.Empty);

						Console.ForegroundColor = ConsoleColor.Cyan;
						Console.WriteLine($">    Type: {cat}");
						Console.ResetColor();

						foreach (var a in attrib.Attributes()) {
							if (a.Name == "name"){ ent.Drive = a.Value; }
							Console.WriteLine($">    {a}");
						}//foreach(var a in attrib.Attributes())

						foreach(var nodes in attrib.Descendants()) {
							string n = Regex.Replace(nodes.Name.ToString(), "{.*?}", String.Empty);

							Console.ForegroundColor = ConsoleColor.Cyan;
							if (!nodes.HasAttributes) { Console.WriteLine($">    Container: {n}"); }
							else { Console.WriteLine($">        {n}"); }
							Console.ResetColor();

							foreach (var node in nodes.Attributes()) {
								Console.WriteLine($">        {node}");
								if (n == "Properties") { // Map Properties
									if (node.Name == "path") { ent.Path = node.Value; }
									if (node.Name == "label") { ent.Label = node.Value; }
								}else if (n == "FilterGroup") { // ILT Properties
									ent.FilterType = "Group";
									if(node.Name == "name") { ent.FilterName = node.Value;  }
									if(node.Name == "sid") { ent.FilterSID = node.Value; }
								}else if(n == "FilterOrgUnit") { // ILT Properties
									ent.FilterType = "OU";
									ent.FilterSID = "";
									// Since exporting to CSV, commas cause problems. Wrap in quotes.
									if(node.Name == "name") { ent.FilterName = "\"" + node.Value + "\""; }
								}
							}//foreach(var node in nodes.Attributes())
							// Deep copy of object into new object to prevent reference issues.
							if (n == "FilterOrgUnit" || n == "FilterGroup") {
								Entry newEnt = new Entry();
								newEnt.GPO = ent.GPO;
								newEnt.Drive = ent.Drive;
								newEnt.Path = ent.Path;
								newEnt.Label = ent.Label;
								newEnt.FilterType = ent.FilterType;
								newEnt.FilterSID = ent.FilterSID;
								newEnt.FilterName = ent.FilterName;
								entries.Add(newEnt); // APPEND ENTRIES LIST
							}
						}//foreach(var node in attrib.Descendants())
					}//foreach(var attrib in el.Elements()) 
				}//foreach(var node in attrib.Nodes())
			}//foreach(var el in xml.Descendants())
			try {
				File.AppendAllLines("ilt.csv", entries.Select(x => x.ToString())); // Save to \bin\Debug
			}
			catch (Exception ex) {
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

	/// <summary>
	/// Class Object for each entry in the list used to write to csv.
	/// </summary>
	class Entry
	{
		public string GPO="", Drive="", Path="", Label="", FilterType="", FilterSID="", FilterName="";
		public override string ToString()
		{
			return $"{GPO},{Drive},{Path},{Label},{FilterType},{FilterSID},{FilterName}";
		}
	}
}
